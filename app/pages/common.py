from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.billing.subscription_period import access_is_open, days_left
from app.config import Settings
from app.dependencies import email_is_admin
from app.constants import (
    ACCESS_SOON_DAYS,
    AD_STATUS_DRAFT,
    AD_STATUS_PUBLISHED,
    MESSENGER_LABELS,
)
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.models.user import User
from app.services.auth_service import actor_id as token_actor_id, decode_access_token
from app.services.s3 import get_image_url

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
_static_dir = Path(__file__).resolve().parent.parent / "static"
templates = Jinja2Templates(directory=str(_templates_dir))

# Глобалы изображений привязываются к настройкам ПРИЛОЖЕНИЯ, а не к окружению
# процесса (D-21). Раньше все три вызывали get_settings() — то есть собирали
# Settings() из `.env` рабочего каталога в обход create_app(settings=...) и
# dependency_overrides. Следствий было два: базовый URL приезжал из окружения
# мимо подменённых настроек, а без файла `.env` рендер /ads/new падал
# ValidationError на обязательных полях (T-02-02).
#
# Почему не параметрическая инъекция по образцу format_datetime_for_user.
# ad_card — это МАКРОС (app/templates/ads/includes/ad_card.html:25), а
# импортированным макросам Jinja контекст вызывающего не передаёт. Передача
# базового URL параметром потребовала бы менять сигнатуру макроса и все его
# вызовы в ads/list.html и ads/partial_cards.html, то есть трогать разметку
# списка ради починки настроек. Привязка на уровне create_app чинит ровно
# заявленный дефект и не касается ни одного шаблона.
#
# ОГРАНИЧЕНИЕ: templates — модульный синглтон, общий на процесс, поэтому
# привязка глобальна и последний create_app выигрывает. Для одного приложения
# на процесс (бой) и для теста, создающего своё приложение в фикстуре, этого
# достаточно. Разведение окружений Jinja по приложениям — архитектурная
# правка, выходящая за границы этого плана.
def _resolve_image_url(key: str, s3_public_url: str) -> str:
    """Return key as-is if it's already a full URL, else build S3 URL."""
    if not key:
        return ""
    if key.startswith("http://") or key.startswith("https://"):
        return key
    return get_image_url(key, s3_public_url)


def _bind_image_url_globals(s3_public_url: str) -> None:
    """Register the three image globals closed over an explicit base URL."""
    templates.env.globals["get_image_url"] = lambda key: get_image_url(key, s3_public_url)
    templates.env.globals["resolve_image_url"] = lambda key: _resolve_image_url(key, s3_public_url)
    templates.env.globals["s3_public_url"] = lambda: s3_public_url


def bind_image_url_globals(settings: Settings) -> None:
    """Bind image template globals to the settings the app actually owns.

    Вызывается из create_app (app/main.py) сразу после разрешения settings.
    """
    _bind_image_url_globals(settings.s3_public_url)


# Безопасный дефолт на импорте: имена существуют с пустым базовым URL, и НИ
# ОДНОГО конструирования Settings на импорте модуля не происходит.
_bind_image_url_globals("")


def _compute_asset_version() -> str:
    """Return a cache-busting suffix for /static links.

    Хешей в именах файлов нет и build-шаг запрещён (D-02), поэтому версия
    берётся от времени изменения app.css и считается один раз при импорте.
    """
    try:
        return str(int((_static_dir / "css" / "app.css").stat().st_mtime))
    except OSError:
        return "dev"


templates.env.globals["asset_version"] = _compute_asset_version()


# Состояние объявления доезжает до шаблонов ГЛОБАЛОМ, по образцу nav_items.
# Карточка объявления — макрос (app/templates/ads/includes/ad_card.html:25), а
# импортированным макросам Jinja контекст вызывающего не передаёт: параметром
# значение пришлось бы протащить через сигнатуру макроса и оба его вызова.
# Литерал, выписанный в шаблоне вручную, лишил бы app/constants.py статуса
# единственного источника — разъехавшись с моделью, он показывал бы
# «Опубликовано» тому, что планировщик не отправляет.
# Конструирования Settings здесь не происходит: значения — модульные константы.
templates.env.globals["AD_STATUS_DRAFT"] = AD_STATUS_DRAFT
templates.env.globals["AD_STATUS_PUBLISHED"] = AD_STATUS_PUBLISHED

# Подписи каналов доезжают до шаблонов тем же способом и по той же причине:
# строка перечня воркеров — МАКРОС, а импортированным макросам Jinja контекст
# вызывающего не передаёт. Довод «макрос обязан быть самодостаточным» запрещает
# рассчитывать на переменную ВЫЗЫВАЮЩЕЙ страницы, но не на глобал окружения —
# и именно глобал снимает копию словаря из разметки, оставляя один источник в
# app/constants.py.
templates.env.globals["messenger_labels"] = MESSENGER_LABELS


# Состав навигации по D-11. Список выписан ОДИН раз и используется и в
# боковом меню (data-nav), и в нижних табах (data-tabs) — иначе переименования
# пришлось бы править в трёх местах, как было в старом шелле.
#
# ПУНКТА «ГРУППЫ» ЗДЕСЬ НЕТ с плана 03-08. Фаза 1 сохранила его временно —
# ровно до появления экрана групп аккаунта, — и это обещание закрыто: группы
# живут ВНУТРИ «Аккаунтов» (`/accounts/{id}/groups`, D-02), вход на них —
# строка аккаунта, а глобальный раздел снесён целиком (D-01). Отдельный пункт
# меню вёл бы на страницу, которой нет.
NAV_ITEMS: list[dict] = [
    {"key": "dashboard", "label": "Дашборд", "href": "/dashboard", "count_key": None},
    {"key": "accounts", "label": "Аккаунты", "href": "/accounts", "count_key": "accounts"},
    {"key": "ads", "label": "Объявления", "href": "/ads", "count_key": "ads"},
    {"key": "schedules", "label": "Расписания", "href": "/schedules", "count_key": "schedules"},
    {"key": "history", "label": "История", "href": "/history", "count_key": "history"},
    # ⚠️ РАЗДЕЛ ПЕРЕИМЕНОВАН ВМЕСТЕ СО СМЕНОЙ ПРЕДМЕТА (план 05.1-05, A-1).
    # Тарифов Free/Basic/Pro не существует (D-F), выбирать не из чего, и прежняя
    # подпись обещала бы выбор, которого нет. Прежнее имя раздела в этом
    # комментарии НЕ НАЗВАНО: гейт переименования читает файл по тексту, и
    # объяснение, набранное старым литералом, роняло бы собственный запрет.
    # Строка выписана ЗДЕСЬ ОДИН раз — отсюда её читают и сайдбар, и нижние
    # табы, и заголовок страницы через `nav_label`, поэтому имя меняется сразу
    # на трёх поверхностях, а не в одной из них.
    {"key": "billing", "label": "Подписка", "href": "/billing", "count_key": None},
    {"key": "profile", "label": "Профиль", "href": "/profile", "count_key": None},
]

ADMIN_NAV_ITEM: dict = {"key": "admin", "label": "Админ-панель", "href": "/admin", "tag": "SYS"}


def nav_label(active_page: str | None) -> str:
    """Return the visible section name for an active_page key."""
    for item in NAV_ITEMS:
        if item["key"] == active_page:
            return item["label"]
    if active_page == ADMIN_NAV_ITEM["key"]:
        return ADMIN_NAV_ITEM["label"]
    return "Broadcaster"


templates.env.globals["nav_items"] = NAV_ITEMS
templates.env.globals["admin_nav_item"] = ADMIN_NAV_ITEM
templates.env.globals["nav_label"] = nav_label


def _get_timezone_for_user(user: User | None) -> ZoneInfo:
    """Return ZoneInfo for user's timezone or UTC as fallback."""
    tz_name = "UTC"
    if user and getattr(user, "timezone", None):
        try:
            tz_name = user.timezone
            return ZoneInfo(tz_name)
        except Exception:
            tz_name = "UTC"
    return ZoneInfo(tz_name)


def format_datetime_for_user(
    value: datetime | None,
    user: User | None,
    fmt: str = "%Y-%m-%d %H:%M",
) -> str:
    """Format datetime in user's timezone for display."""
    if value is None:
        return ""
    # Если дата без tzinfo — считаем, что она в UTC
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    tz = _get_timezone_for_user(user)
    local = value.astimezone(tz)
    return local.strftime(fmt)


templates.env.globals["format_datetime_for_user"] = format_datetime_for_user


def plural_ru(count: int, one: str, few: str, many: str) -> str:
    """Return the Russian noun form matching `count`.

    Общего хелпера склонений в проекте не было: единственный случай был решён
    конкатенацией одной формы (`sched_card.html`). Линейка счётчика экрана
    групп обязана печатать «1 активная из 1 группы», а не «1 активных из 1
    групп» (UI-SPEC §Copywriting Contract, E3 zero-one-many), поэтому форма
    выбирается по числу, а не выписывается в разметке.

    Хелпер возвращает ТОЛЬКО форму слова и ничего не форматирует: число рядом с
    ней ставит вызывающий шаблон. Так один и тот же хелпер обслуживает и
    «5 активных», и «в 3 расписаниях», где число стоит в разных местах строки.
    """
    tail = abs(int(count)) % 100
    if 11 <= tail <= 14:
        return many
    tail %= 10
    if tail == 1:
        return one
    if 2 <= tail <= 4:
        return few
    return many


templates.env.globals["plural_ru"] = plural_ru


def time_ago_for_user(value: datetime | None, user: User | None) -> str:
    """Return a short Russian «N назад» string for a past moment.

    Шапка экрана групп обязана читаться «последняя синхронизация 2 часа назад»
    (UI-SPEC §Header card). Абсолютное форматирование
    (`format_datetime_for_user`) для этого не годится, а клиентских часов в
    проекте нет и заводить их не за чем: таймзона пользователя уже решена
    хелперами этого модуля, поэтому разница считается на сервере.

    Пустое значение отдаёт ПУСТУЮ строку, а не «0 минут назад»: «синхронизация
    ещё не выполнялась» — отдельная ветка разметки, и выдуманный ноль подменил
    бы её правдоподобной ложью (Pitfall 2).

    Момент из будущего (часы сервера и базы разошлись) читается «только что»:
    отрицательная разница напечатала бы «-1 минуту назад».
    """
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    tz = _get_timezone_for_user(user)
    seconds = int((datetime.now(tz) - value.astimezone(tz)).total_seconds())

    minutes = seconds // 60
    if minutes < 1:
        return "только что"
    if minutes < 60:
        return f"{minutes} {plural_ru(minutes, 'минуту', 'минуты', 'минут')} назад"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} {plural_ru(hours, 'час', 'часа', 'часов')} назад"
    days = hours // 24
    return f"{days} {plural_ru(days, 'день', 'дня', 'дней')} назад"


templates.env.globals["time_ago_for_user"] = time_ago_for_user


# Разделитель разрядов и отбивка перед знаком рубля — НЕРАЗРЫВНЫЙ пробел:
# обычный перенёс бы «1» и «490» на разные строки узкой карточки тарифа.
_NBSP = "\u00a0"


def format_amount(value) -> str:
    """Денежная сумма ПОДПИСЬЮ: «1490.00» → «1 490 ₽».

    ФОРМАТИРОВАНИЕ ЖИВЁТ ТОЛЬКО НА СТОРОНЕ ПОКАЗА. В конфиге тарифов и пакетов
    цена хранится машинной строкой формата ЮKassa, и `create_payment` кладёт
    её прямо в `amount.value`: строка с разделителем разрядов или знаком рубля
    — отказ платёжного API в проде, который не поймает ни один мок на моках
    (05-RESEARCH A3). Поэтому обратной функции здесь нет и быть не должно:
    подпись никогда не едет обратно в платёж.

    Нулевые копейки не показываются: «1 490 ₽» вместо «1 490,00 ₽» — так же,
    как в макете. Ненулевые показываются через запятую, потому что потерять
    полтинник на экране хуже, чем показать лишние два знака.

    Непригодное значение возвращается КАК ЕСТЬ, а не заменяется нулём:
    выдуманный ноль в денежной подписи — правдоподобная ложь, а исходная
    строка на экране хотя бы называет себя странной.

    ПРОВЕРКА КОНЕЧНОСТИ СТОИТ ПОСЛЕ РАЗБОРА, А НЕ ВМЕСТО НЕГО. `NaN` и
    `Infinity` — валидные значения `Decimal`, и `except` вокруг разбора их не
    видит: до плана 05-09 они уходили из-под защиты и роняли форматирование
    ниже. Функция — глобал Jinja на трёх поверхностях раздела сразу, поэтому
    одна такая строка в конфиге цен или в `payments.amount_value` уводила
    `/billing` в 500 целиком.
    """
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        return str(value)
    if not amount.is_finite():
        return str(value)

    sign = "-" if amount < 0 else ""
    whole, _, kopecks = f"{abs(amount):.2f}".partition(".")
    groups = f"{int(whole):,}".replace(",", _NBSP)
    tail = "" if kopecks == "00" else f",{kopecks}"
    return f"{sign}{groups}{tail}{_NBSP}₽"


templates.env.globals["format_amount"] = format_amount

# ПОРОГ «СКОРО КОНЧИТСЯ» ПРИЕЗЖАЕТ В РАЗМЕТКУ КОНСТАНТОЙ, А НЕ ЛИТЕРАЛОМ (D-K).
# Внутри порога виджет доступа показывает ДНИ, вне — ДАТУ, и это же число
# читает вердикт. Выписанная в шаблоне семёрка была бы второй копией правила и
# разошлась бы с первой молча — то есть виджет предупреждал бы не тогда, когда
# предупреждает система. То же основание, по которому строка отказа `pending`
# не называет число часов давности.
templates.env.globals["access_soon_days"] = ACCESS_SOON_DAYS


# ИМЯ ПОЛЯ, КОТОРЫМ СУБЪЕКТ НЕСЁТ СВОЁ ДЕЙСТВУЮЩЕЕ ЛИЦО, — ОДНО НА ПРОЕКТ.
#
# ⚠️ ПОЛЕ НЕ КОЛОНКА И В БАЗУ НЕ ПИШЕТСЯ. Это обычный атрибут экземпляра:
# отображение SQLAlchemy знает только свои колонки, и посторонний атрибут не
# попадает ни в один запрос. Живёт он ровно столько, сколько живёт объект
# пользователя внутри запроса.
#
# ЗАЧЕМ ИМЕННО ТАК, А НЕ ЛИШНИМ ПАРАМЕТРОМ У ПРОВЕРКИ ПРАВ. Проверку прав зовут
# пятнадцать обработчиков в шести модулях, и все — в форме `check_is_admin(user,
# settings)`. Новый параметр пришлось бы дописать в каждый вызов, а забытый
# вызов выглядел бы совершенно исправным: администратор просто терял бы права
# ровно на одной странице. Действующее лицо поэтому едет ВМЕСТЕ с субъектом,
# которого проверка и так получает, и ставит его ЕДИНСТВЕННАЯ точка чтения
# токена на страничном пути.
IMPERSONATOR_ATTR = "impersonated_by"

# ПОТОЛОК ПОДПИСИ В ПОЛОСЕ ВОЗВРАТА. Имя пользователя — произвольный ввод, а
# полоса рисуется на КАЖДОМ из 26 страничных маршрутов: имя в двести знаков
# растянуло бы её на несколько строк над каждым экраном продукта. Усечение
# живёт в обработчике, а не в разметке, — величина, обрезанная в шаблоне,
# обрезалась бы по-разному в каждом месте показа.
IMPERSONATION_LABEL_CAP = 48


async def get_user_from_cookie(
    request: Request, db: AsyncSession, settings: Settings
) -> User | None:
    """Кто пришёл на СТРАНИЧНОМ пути — единственная точка чтения токена страниц.

    ⚠️ БЛОКИРОВКА ПРИМЕНЯЕТСЯ К СУБЪЕКТУ, НО НЕ ПРИ НАЛИЧИИ ДЕЙСТВУЮЩЕГО ЛИЦА
    (D-26). Вход администратора под ЗАБЛОКИРОВАННЫМ пользователем разрешён
    ЯВНЫМ решением: «за что меня заблокировали» — типовой вопрос, и ответить на
    него можно, только увидев продукт глазами заблокированного. До этой ветки
    администратор, вошедший под заблокированным, был неотличим от невошедшего —
    молчаливый редирект на вход без единого слова о причине (стык, записанный
    планом 06-06 в `deferred-items.md`).

    ⚠️ ГРАНИЦА СНИЗУ ТОЙ ЖЕ ВЕТКИ: без действующего лица блокировка действует
    ровно как прежде. Закрытость страничной формы покупки для заблокированного
    есть ПОБОЧНЫЙ ЭФФЕКТ этой функции, и до плана 06-12 она не была закреплена
    ничем — теперь закреплена
    `test_the_page_purchase_form_stays_closed_to_a_blocked_user`.

    ⚠️ ДЕЙСТВУЮЩЕЕ ЛИЦО ПРИСВАИВАЕТСЯ ВСЕГДА, В ТОМ ЧИСЛЕ ПУСТЫМ ЗНАЧЕНИЕМ, И
    ЭТО НЕ ИЗБЫТОЧНОСТЬ. Объект пользователя живёт в карте тождества сессии и
    переживает несколько запросов, когда сессия одна на несколько обращений
    (так устроена тестовая фикстура). Присвоение «только при имперсонации»
    оставило бы вчерашнее действующее лицо на объекте после ВОЗВРАТА — то есть
    администратор, вышедший из чужой личности, продолжал бы числиться
    действующим за неё.

    ЦЕНА НАЗВАНА: при имперсонации функция делает ВТОРОЕ чтение строки по
    первичному ключу — самого действующего лица. Оно нужно проверке прав, а не
    полосе возврата: админство есть совпадение АДРЕСА с настройкой, и адрес
    берётся только из строки. Обычный запрос (без признака) не платит ничего.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token, settings.secret_key)
    if not payload:
        return None
    user = await db.get(User, payload["sub"])
    if user is None:
        return None

    actor_id = token_actor_id(payload)
    actor = await db.get(User, actor_id) if actor_id is not None else None
    setattr(user, IMPERSONATOR_ATTR, actor)

    if actor is None and user.is_blocked:
        return None
    return user


def actor_of(user: User | None) -> User | None:
    """Кто ДЕЙСТВУЕТ от имени этого пользователя, либо `None`.

    Единственный читатель поля на проект. Потребители спрашивают «кто
    действует», а не «есть ли у объекта такой атрибут»: второе — знание об
    устройстве, и первый же скопировавший его читатель завёл бы второе
    объявление правила.
    """
    if user is None:
        return None
    return getattr(user, IMPERSONATOR_ATTR, None)


def check_is_admin(user: User | None, settings: Settings) -> bool:
    """Админ ли ТОТ, КТО ДЕЙСТВУЕТ (D-20) — страничная проверка прав.

    ⚠️ ПРАВА ЧИТАЮТСЯ ПО ДЕЙСТВУЮЩЕМУ ЛИЦУ, А НЕ ПО СУБЪЕКТУ, И ЭТО И ЕСТЬ
    ИСПОЛНЕНИЕ КРИТЕРИЯ «НЕ ТЕРЯЯ АДМИН-ДОСТУП». Админство сегодня есть
    совпадение адреса пользователя с настройкой; под чужой учётной записью
    субъект — чужой человек, и права исчезли бы вместе с личностью, заперев
    администратора в чужой учётке без пути назад.

    Частный случай «действующего лица нет» ДЕМОТИРОВАН до «действующее лицо
    равно субъекту» и обслуживается той же веткой. Отдельная ветка «если
    имперсонации нет» была бы вторым выражением одного правила: разойтись им
    есть на чём, и разошлись бы они молча.

    Закреплено инвариантом
    `test_admin_ness_is_decided_by_the_actor_and_otherwise_by_the_subject` —
    обе половины правила в одном теле.

    ⚠️ САМО СРАВНЕНИЕ ЗДЕСЬ НЕ ВЫПИСАНО: оно живёт в `email_is_admin`
    (`app/dependencies.py`) — единственном выражении правила «кто
    администратор» на проект. Пока копий было две, они разошлись веткой
    «настройка не задана», и разошлись в сторону выдачи доступа (WR-01
    ревизии фазы 6). Здесь остаётся то, чего у зависимости нет и быть не
    должно: ВЫБОР ЛИЦА, о правах которого спрашивают.
    """
    actor = actor_of(user) or user
    if actor is None:
        return False
    return email_is_admin(actor.email, settings)


def impersonation_view(user: User | None) -> dict:
    """Признак имперсонации для шелла — или пустой словарь.

    ⚠️ ЗАПРОСОВ НЕ ДЕЛАЕТ ВОВСЕ, И ЭТО ПРОВЕРЯЕМОЕ СВОЙСТВО, А НЕ НАМЕРЕНИЕ: у
    функции нет сессии БД в параметрах, поэтому обратиться к базе ей нечем.
    Полоса возврата рисуется на КАЖДОМ из 26 страничных маршрутов, и запрос
    ради неё оплачивался бы на каждом рендере продукта — в том числе у 100%
    пользователей, которые под чужой личностью не находятся никогда.

    ⚠️ НЕТ ДЕЙСТВУЮЩЕГО ЛИЦА — НЕТ КЛЮЧА, а не ключ с пустым значением. Полоса
    рисуется по наличию ключа; ложная полоса «вы работаете от имени» на 26
    страницах хуже её отсутствия — она сообщает человеку, что его действия
    уходят от чужого имени, когда это неправда.

    ⚠️ ПОДПИСЬ НИКОГДА НЕ ПУСТА. У пользователя может не быть имени, и полоса
    «Вы работаете от имени пользователя » — это подпись, не называющая никого.
    Тогда печатается адрес: он есть всегда.
    """
    actor = actor_of(user)
    if actor is None or user is None:
        return {}

    label = (user.name or "").strip() or user.email
    if len(label) > IMPERSONATION_LABEL_CAP:
        label = label[: IMPERSONATION_LABEL_CAP - 1].rstrip() + "…"

    return {
        "impersonation": {
            "actor_id": actor.id,
            "subject_id": user.id,
            "subject_label": label,
        }
    }


def is_same_origin(request: Request) -> bool:
    """Пришёл ли изменяющий запрос со страницы САМОГО приложения (T-04-38, T-05-06).

    ЗАЧЕМ. Аутентификация проекта идёт cookie, поэтому браузер прикладывает её к
    межсайтовой форме сам, и изменяющий запрос со стороннего сайта неотличим от
    своего. ASVS L1 (V4.2.2) требует защиты изменяющих состояние запросов от
    межсайтовой подделки. Сверка заголовков — единственный вариант, который не
    требует ни схемы токенов на весь проект, ни правки шаблонов, ни новой
    зависимости.

    ПРАВИЛО. Пришёл `Sec-Fetch-Site` — принимается только значение
    `same-origin`, всё прочее отклоняется. Иначе пришёл `Origin` — его ХОСТ
    обязан совпасть с хостом самого запроса. Сравнивается именно хост, а не
    строка целиком: заголовок источника несёт схему и порт, адрес запроса —
    тоже, и посимвольное сравнение сломалось бы на первом же развёртывании за
    обратным прокси. Хост своего адреса берётся ИЗ ЗАПРОСА, а не из настроек:
    поля с базовым адресом приложения в настройках проекта нет, и заводить его
    ради одной проверки значило бы завести конфигурацию, которую придётся
    сопровождать.

    ⚠️ НАЗВАННАЯ ГРАНИЦА ЗАЩИТЫ. Запрос, не приславший НИ ОДНОГО из двух
    заголовков, пропускается. Браузер, способный отправить межсайтовую форму,
    шлёт `Origin` на POST начиная с 2016 года, поэтому отсутствие обоих
    заголовков означает не-браузерного клиента — в том числе тестовую суиту
    проекта, которая их не шлёт. Отказ по их отсутствию не добавил бы ни одной
    защиты и покрасил бы весь остальной путь. Ограничение выписано здесь и
    продублировано в отчёте безопасности фазы намеренно: принятый риск, о
    котором не написано, через один рефакторинг становится неизвестным.

    ⚠️ РАМКИ. Гард живёт ПУБЛИЧНЫМ именем здесь, чтобы у правила был ОДИН
    источник на проект. Потребителей три, и все зовут эту функцию: форма
    покупки тарифа, форма покупки пакета сообщений (обе —
    `app/pages/billing.py`) и повтор отправки (`app/pages/history.py`).
    Приватная копия, жившая в `history.py` с плана 04-10, снята планом 05-04:
    второй экземпляр правила означал бы, что правку одного гарда придётся не
    забыть повторить в другом, а забытая половина выглядела бы работающей.

    ⚠️ ПЕРЕЧЕНЬ ПОТРЕБИТЕЛЕЙ ЗДЕСЬ БОЛЬШЕ НЕ ВЕДЁТСЯ, И ЭТО ОСОЗНАННО. Он был
    списком из трёх имён, разошедшимся с кодом ровно тогда, когда фаза 6
    добавила в админку шесть изменяющих маршрутов: половина взяла гард,
    половина — нет, а комментарий продолжал называть три. Полноту теперь держит
    МАШИННЫЙ ГЕЙТ `test_every_mutating_admin_route_checks_the_origin`
    (`tests/test_pages/test_admin_panel.py`), читающий исходник: изменяющий
    маршрут админки без вызова гарда роняет тест вместо того, чтобы оказаться
    открытым по умолчанию. Форма та же, что у гейта запретов под чужой
    личностью (D-23), и по той же причине.

    Прежний остаток «удаления через POST гарда не получают» ЗАКРЫТ: блокировка,
    удаление и выдача бесплатного доступа несут гард с ревизии фазы 6 (CR-02).
    """
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site:
        return fetch_site == "same-origin"
    origin = request.headers.get("origin")
    if origin:
        return urlsplit(origin).hostname == request.url.hostname
    return True


# Предикат «воркер онлайн» объявлен ОДИН раз. Значение дословно повторяет то,
# что раньше было захардкожено в счётном подзапросе get_shell_context: перечень
# и агрегат обязаны решать «онлайн ли он» одним и тем же сравнением, иначе
# пилюля шапки и строка перечня разошлись бы на одном и том же аккаунте.
WORKER_ONLINE_STATUS = "active"

# Потолок ПЕРЕЧНЯ воркеров, уезжающего в разметку. Число строк задаёт
# пользователь — схема не ограничивает, сколько messenger-аккаунтов он заведёт,
# — а контракт шелла собирается на КАЖДОМ из 26 маршрутов страниц, включая 25,
# которые перечня не читают вовсе. Выборка без потолка означала бы выделение
# памяти и разметку, растущие вместе с числом аккаунтов, на каждом рендере
# продукта: не «медленно», а неограниченно по управляемому пользователем входу.
#
# Сто — с большим запасом больше, чем бывает у живого пользователя, и заведомо
# меньше, чем нужно, чтобы это стало заметно. Перебравший потолок НЕ узнаёт об
# этом молча: `sessions_truncated` уезжает в контекст, и перечень говорит, что
# показан не целиком (тот же принцип, что у потолка выгрузки истории — обрезка
# обязана называть себя).
WORKER_LIST_CAP = 100


async def get_shell_context(db: AsyncSession, user: User | None) -> dict:
    """Collect live shell data: nav counts, access period and messenger sessions.

    Публичный контракт живых данных шелла (D-09/D-19). Фаза 4 (DASH-05) и
    Фаза 6 переиспользуют его, а не пишут своё чтение.

    Ключи sessions_online / sessions_total измеряют состояние СЕССИИ
    мессенджера (MessengerAccount.status в БД), а не состояние
    Docker-контейнера. Перечисление контейнеров воркеров здесь не
    вызывается ни при каких условиях: это синхронный Docker SDK, он
    блокирует event loop на рендере каждой страницы, а в тестах сокет
    Docker недоступен.

    Контракт отдаёт и ПЕРЕЧЕНЬ `sessions` — по строке на messenger-аккаунт
    владельца, не более WORKER_LIST_CAP строк, — а sessions_online /
    sessions_total считаются агрегатами и от потолка перечня не зависят: иначе
    пользователь за потолком видел бы в шапке заниженное число, то есть цифру,
    которая молча врёт. ПРЕДИКАТ «онлайн» у перечня и у агрегата ОДИН
    (WORKER_ONLINE_STATUS): разойтись им не на чем, и это то, что обещает D-35, —
    одно определение предиката, а не одно физическое чтение.

    Признак `sessions_truncated` говорит, что перечень показан не целиком.
    """
    if user is None:
        return {}

    # Один round-trip на счётчики сущностей: скалярные подзапросы без FROM.
    # Оба числа по messenger-аккаунтам считаются ЗДЕСЬ, а не длиной перечня
    # ниже: перечень ограничен потолком, и выведенные из него агрегаты за
    # потолком показывали бы пользователю не то число аккаунтов, которое у него
    # есть. Предикат «онлайн» при этом остаётся ОДНИМ (WORKER_ONLINE_STATUS) —
    # сравнение то же самое, что у строки перечня.
    counts = (
        await db.execute(
            select(
                select(func.count())
                .select_from(Ad)
                .where(Ad.user_id == user.id)
                .scalar_subquery()
                .label("ads"),
                # У Schedule нет user_id — принадлежность идёт через Ad,
                # как во всех запросах app/pages/schedules.py.
                select(func.count())
                .select_from(Schedule)
                .join(Ad, Schedule.ad_id == Ad.id)
                .where(Ad.user_id == user.id)
                .scalar_subquery()
                .label("schedules"),
                select(func.count())
                .select_from(SendLog)
                .where(SendLog.user_id == user.id)
                .scalar_subquery()
                .label("history"),
                select(func.count())
                .select_from(MessengerAccount)
                .where(MessengerAccount.user_id == user.id)
                .scalar_subquery()
                .label("accounts"),
                select(func.count())
                .select_from(MessengerAccount)
                .where(
                    MessengerAccount.user_id == user.id,
                    MessengerAccount.status == WORKER_ONLINE_STATUS,
                )
                .scalar_subquery()
                .label("accounts_online"),
            )
        )
    ).one()

    # Состояние воркеров ПОАККАУНТНО — одно обращение по индексированному
    # user_id, возвращающее единицы строк (DASH-05).
    #
    # Проекция ровно трёх колонок — не оптимизация, а ГРАНИЦА: credentials
    # хранит строку сессии Telegram и телефон MAX/WhatsApp, session_data —
    # состояние сессии, а этот словарь печатается в HTML на каждой из 26
    # страниц. ORM-объект целиком затащил бы секреты на экран.
    #
    # Предикат user_id — второй слой владения, а не украшение: перечень чужих
    # аккаунтов показал бы, каким каналом пользуется другой пользователь.
    #
    # Порядок по id — чтобы разметка была детерминированной.
    #
    # ПОТОЛОК ОБЯЗАТЕЛЕН: перечень читает ОДИН маршрут из 26, а собирается он на
    # всех, и число строк задаёт пользователь. Без `limit` это выделение памяти
    # и разметка, растущие вместе с числом его аккаунтов, на каждом рендере
    # продукта.
    worker_rows = (
        await db.execute(
            select(
                MessengerAccount.id,
                MessengerAccount.type,
                MessengerAccount.status,
            )
            .where(MessengerAccount.user_id == user.id)
            .order_by(MessengerAccount.id)
            .limit(WORKER_LIST_CAP)
        )
    ).all()
    sessions = [
        {
            "id": row.id,
            "type": row.type,
            "status": row.status,
            "is_online": row.status == WORKER_ONLINE_STATUS,
        }
        for row in worker_rows
    ]

    subscription = (
        await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # ВЕРДИКТ СНИМАЕТСЯ ЕДИНСТВЕННЫМ ПРЕДИКАТОМ ПРОЕКТА, а не вторым сравнением
    # дат на этом месте. Разойдясь на строгости сравнения или на признаке
    # активности строки, две копии правила выдали бы разные ответы, и виджет на
    # 26 страницах обещал бы доступ ровно тогда, когда зависимость
    # `require_access` в нём уже отказывает. Момент времени берётся ОДИН на весь
    # словарь: вердикт и остаток дней, посчитанные от разных `now`, могли бы
    # разъехаться на границе суток (T-05.1-19).
    now = datetime.now(timezone.utc)
    expires_at = subscription.expires_at if subscription else None

    return {
        "nav_counts": {
            "ads": counts.ads,
            "accounts": counts.accounts,
            "schedules": counts.schedules,
            "history": counts.history,
        },
        # СРОК ДОСТУПА, А НЕ КВОТА СООБЩЕНИЙ. Ключ переименован вместе со сменой
        # ФОРМЫ значения ({used, limit, percent, plan} → {open, expires_at,
        # days_left}), а не подписи: имя `quota` над словарём без квоты — та же
        # ложь, за которую фаза 5 сняла виджет с чужой подписью (D-22, A-10).
        #
        # УМОЛЧАНИЙ У ВЕРДИКТА НЕТ. Пользователь без строки подписки получает
        # `False` / `None` / `None`, а не выдуманное имя тарифа, которое здесь
        # подставлялось прежде: отсутствие строки — это ОПРЕДЕЛЁННОЕ состояние
        # (доступа нет), и оно переживёт выкат ревизии (D-G, П-о-1).
        #
        # ФОРМА КЛЮЧА СТАЛА ПОЛНОЙ ПЛАНОМ 05.1-09 (D-E, UI-контракт C3): признак
        # выданной администратором льготы приезжает ВМЕСТЕ со своей колонкой.
        # Дополнительного запроса не появилось — строка подписки уже прочитана
        # выше, и признак снимается с неё же. Порядок ключей повторяет порядок
        # чтения, а не важности: вердикт, дата, признак, остаток суток.
        #
        # ⚠️ ПРИЗНАК ЕДЕТ СЮДА, ЧТОБЫ ЕГО ПОКАЗАТЬ, А НЕ ЧТОБЫ ПО НЕМУ РЕШАТЬ.
        # Решение принимает `access_is_open` строкой выше — единственное
        # объявление правила доступа на проект; поверхности показа (виджет
        # сайдбара, панель раздела) читают ГОТОВЫЙ вердикт и этот признак как
        # подпись к нему. Ветка «если льгота — считай доступ открытым», выписанная
        # в разметке или на странице, была бы вторым выражением того же правила.
        "access": {
            "open": access_is_open(subscription, now),
            "expires_at": expires_at,
            "is_comped": bool(subscription.has_free_access) if subscription else False,
            "days_left": days_left(expires_at, now),
        },
        # Перечень ограничен потолком, агрегаты — нет: числу в шапке нельзя
        # зависеть от того, сколько строк поместилось в перечень.
        "sessions": sessions,
        "sessions_online": counts.accounts_online,
        "sessions_total": counts.accounts,
        # Обрезка обязана НАЗЫВАТЬ СЕБЯ: молча короткий перечень читался бы как
        # «остальных аккаунтов нет», то есть как ответ на вопрос, ради которого
        # пользователь и пришёл на дашборд.
        "sessions_truncated": counts.accounts > len(sessions),
        # ПРИЗНАК ИМПЕРСОНАЦИИ ПРИЕЗЖАЕТ СЮДА ТЕМ ЖЕ ПРИЁМОМ, ЧТО ДОСТУП И
        # СЧЁТЧИКИ, — и ровно поэтому полоса возврата видна на КАЖДОЙ из 26
        # страниц, а не только в админке. Дополнительного запроса он не стоит:
        # действующее лицо уже прочитано единственной точкой чтения токена
        # (`get_user_from_cookie`), а подпись берётся с самого пользователя,
        # который здесь и так на руках.
        #
        # Раскрытие словарём, а не отдельным ключом: при отсутствии
        # действующего лица ключа НЕ появляется вовсе, и разметка молчит — так
        # же, как молчит виджет доступа при отсутствии своего ключа.
        **impersonation_view(user),
    }
