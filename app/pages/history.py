import csv
import io
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    FAILED_STATUSES,
    HISTORY_PERIODS,
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
    apply_history_filters,
    history_count,
    history_filter_params,
)
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.user import User
from app.pages.common import (
    check_is_admin,
    format_datetime_for_user,
    get_user_from_cookie,
    templates,
)
from app.services.billing_cache import check_balance_cached

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30

# --- Оси фильтрации: значения и подписи ---------------------------------------
#
# Перечни объявлены ЗДЕСЬ, а не в шаблоне (тот же приём, что у осей сводного
# списка расписаний): неизвестное значение обязано отсекаться сервером, а
# разметка точкой принуждения не является — она только рисует. Из этих же
# перечней строятся допустимые наборы `_clean_choice`, поэтому нарисованное и
# принимаемое разойтись не могут в принципе.

# Три значения журнала, а не два. Прежний выпадающий список знал «Успешные» и
# «Ошибки» и терял `account_disconnected` — единственный статус, по которому
# видно, что отправка не ушла из-за отвалившегося аккаунта. Набор СОБИРАЕТСЯ из
# констант модуля аналитики: четвёртый статус, заведённый там, обязан здесь
# упасть по KeyError, а не потеряться молча.
STATUS_LABELS = {
    STATUS_OK: "Успешно",
    STATUS_FAIL: "Ошибка",
    STATUS_ACCOUNT_DISCONNECTED: "Аккаунт отключён",
}
STATUS_CHIPS = (("", "Все"),) + tuple(
    (value, STATUS_LABELS[value]) for value in (STATUS_OK,) + FAILED_STATUSES
)

# Значения канала — те же, что у `MessengerAccount.type` и у оси канала
# сводного списка расписаний (`app.pages.schedules.CHANNEL_FILTER_VALUES`);
# подписи — те же слова, что печатают предпросмотр объявления и раздел
# аккаунтов. Совпадение значений с осью расписаний закреплено тестом, а не
# импортом: ось расписаний описывает ДРУГОЙ экран, и связывать их импортом
# значило бы объявить одну осью другой.
MESSENGER_CHIPS = (
    ("", "Все"),
    ("tg_user", "Telegram"),
    ("wa", "WhatsApp"),
    ("max", "MAX"),
)

# Произвольного диапазона дат нет (D-30): четыре варианта и ни одного поля
# ввода даты. Порядок «сегодня → 7 дней → 30 дней → всё время» — от узкого к
# широкому, как в макете; «всё время» стоит последним, потому что это снятие
# фильтра, а не самый широкий период.
PERIOD_LABELS = {"today": "Сегодня", "7d": "7 дней", "30d": "30 дней"}
PERIOD_CHIPS = tuple((value, PERIOD_LABELS[value]) for value in HISTORY_PERIODS) + (
    ("", "Всё время"),
)


def _values(chips) -> frozenset[str]:
    """Допустимые значения оси без варианта «все»."""
    return frozenset(value for value, _ in chips if value)


STATUS_VALUES = _values(STATUS_CHIPS)
MESSENGER_VALUES = _values(MESSENGER_CHIPS)
PERIOD_VALUES = _values(PERIOD_CHIPS)


def _clean_choice(value: str | None, allowed: frozenset[str]) -> str | None:
    """Неизвестное или испорченное значение оси → «фильтр не применён».

    Значение приезжает строкой запроса, то есть из ссылки, закладки или чужого
    сообщения (T-04-23). Отказ страницы был бы здесь отказом в обслуживании по
    подконтрольному отправителю значению, а молча применённый мусор — пустым
    списком, в котором НИ ОДИН чипс не отмечен активным: по такому экрану не
    прочитать, что вообще произошло. Оба исхода хуже, чем «мусор не выбирает
    ничего», и последнее ровно то же, что делает ось канала сводного списка
    расписаний.

    Период отсекается той же дорогой, хотя модуль аналитики и сам не применяет
    отсечку по неизвестному периоду: без отсечки здесь мусорный период доехал
    бы до адреса чипса и до сентинеля прокрутки как действующий фильтр.
    """
    if not value:
        return None
    value = value.strip()
    return value if value in allowed else None


def _parse_account_id(v: str | None) -> int | None:
    """Разбор HTTP-параметра, а не аналитика — поэтому остаётся здесь.

    Определение самих фильтров переехало в
    `app/application/analytics/send_analytics.py` (D-35): его зовут и история,
    и админка, и счётчик, и ни один из них не владеет копией. Этот же хелпер
    знает про то, что `account_id` приезжает строкой из query-строки, — знание
    транспорта, которому в слое аналитики не место.
    """
    if not v or not v.strip():
        return None
    try:
        return int(v)
    except ValueError:
        return None


# --- Выгрузка истории в файл --------------------------------------------------
#
# HIST-03. Экспорта в проекте не существовало вовсе, поэтому вместе с
# возможностью появляется новый для проекта класс угрозы — см. `export_cell`.

# Подписи колонок в порядке D-28. Снапшота ТЕЛА объявления среди них нет
# намеренно: он раздувает файл в разы и ломает сетку переводами строк внутри
# значения — открытый в редакторе файл рассыпался бы на строки, которых не
# было. Заголовка объявления для узнавания записи достаточно.
EXPORT_HEADER = (
    "Время",
    "Канал",
    "Аккаунт",
    "Группа",
    "Заголовок объявления",
    "Статус",
    "Ошибка",
    "Идентификатор задачи",
)

# Разделитель полей — ТОЧКА С ЗАПЯТОЙ, а не запятая (Open Question 2 плана).
# Метка порядка байтов решает вопрос КОДИРОВКИ, но не разделителя: в русской
# локали табличный редактор берёт разделитель списка из системных настроек, и
# файл с запятыми открывается одной колонкой — то есть намерение D-25 «Excel
# открывает нормально» выполнялось бы ровно наполовину и молча. Значение вынесено
# константой, потому что оно видимо пользователю и может быть пересмотрено одной
# правкой.
EXPORT_DELIMITER = ";"

# Метка порядка байтов UTF-8 (D-25). Записана ЭКРАНОМ, а не самим символом:
# сам символ невидим в исходнике, и потерянный при правке он не оставил бы в
# диффе ни следа — а без него кириллица в редакторе приезжает мусором.
EXPORT_BOM = "\ufeff"

# Потолок числа строк (D-27, значение — Claude's Discretion из названной там
# окрестности). Превышение НЕ обрезает файл: обрезка неотличима от полной
# выгрузки, и пользователь унёс бы неполные данные, не узнав об этом.
EXPORT_ROW_CAP = 50_000

# Имя файла ПОСТОЯННОЕ и не собирается из значений пользователя (T-04-34):
# подстановка в заголовок ответа невозможна по построению.
EXPORT_FILENAME = "history.csv"

# Размер партии потокового чтения. На asyncpg включает серверный курсор, на
# aiosqlite — буферизацию батчами; интерфейс `session.stream` одинаков на обоих
# (тот же приём, что у окна heatmap).
EXPORT_YIELD_PER = 500

# Признак «выгрузка не состоялась из-за потолка», приезжающий на список
# перенаправлением. Значение сравнивается ЦЕЛИКОМ — любое другое содержимое
# параметра игнорируется, как и мусор в осях фильтрации.
EXPORT_TOO_MANY = "too_many"

# Символы, с которых табличный редактор начинает ИСПОЛНЯТЬ содержимое ячейки.
_EXPORT_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

# Подписи канала — те же слова, что печатают чипсы фильтра: одно и то же
# значение обязано называться на экране и в файле одинаково.
MESSENGER_LABELS = {value: label for value, label in MESSENGER_CHIPS if value}


def export_cell(value: object) -> str:
    """Готовит одно значение к записи в файл выгрузки (T-04-16).

    НОВЫЙ ДЛЯ ПРОЕКТА КЛАСС УГРОЗЫ. Заголовок объявления, имя группы и текст
    ошибки приходят от пользователя и от стороннего мессенджера. Табличный
    редактор ИСПОЛНЯЕТ содержимое ячейки, начинающееся с символа формулы, и
    делает это на машине того, кто файл открыл, — не обязательно того, кто его
    выгрузил. Ведущий апостроф переводит значение в текст: редактор его
    показывает, но не исполняет.

    Управляющие символы табуляции и возврата каретки перечислены вместе с
    символами формулы не для красоты: ими открывается известный обход проверки
    «начинается ли значение с равно», после которого редактор всё равно видит
    формулу.

    `None` и пустое значение дают ПУСТУЮ строку, а не слово «None»:
    `error_message` пуст у каждой успешной отправки, то есть у большинства
    строк файла.
    """
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    if text[0] in _EXPORT_DANGEROUS_PREFIXES:
        return "'" + text
    return text


def export_row(log: SendLog, group: Group | None, user: User | None) -> list[str]:
    """Строка файла выгрузки для одной записи журнала — ровно по `EXPORT_HEADER`.

    ФУНКЦИЯ ЧИСТАЯ: в базу не ходит, `Request` не читает. Всё, что ей нужно,
    приезжает аргументами, поэтому состав строки проверяется без сессии, а
    потоковый генератор маршрута не обрастает логикой.

    Аккаунт выводится ЧЕРЕЗ ГРУППУ: колонки аккаунта в журнале нет вовсе, и
    связь эта — единственная. Группа приезжает отдельным аргументом, а не
    берётся с `log`: запрос выбирает пару `SendLog, Group` внешним соединением,
    и у записи с удалённой группой второй элемент пары пуст. Пустая группа даёт
    пустые ячейки и НЕ поднимает исключение: исключение оборвало бы уже начатый
    поток, отдав пользователю обрезанный файл со статусом успеха.

    Время форматируется тем же хелпером, что и разметка записи, — значение в
    файле обязано совпадать с тем, что пользователь видел на экране (D-30).

    Статус и канал печатаются ПОДПИСЯМИ, а незнакомое значение — как есть.
    Пустая ячейка вместо неопознанного значения была бы тем самым молчаливым
    выбрасыванием, которое запрещает прохибиция P-04-01: строка осталась бы в
    файле без единого признака того, чем кончилась отправка.
    """
    return [
        export_cell(format_datetime_for_user(log.sent_at, user)),
        export_cell(MESSENGER_LABELS.get(log.messenger_type, log.messenger_type)),
        export_cell(group.account_id if group else None),
        export_cell(log.group_name),
        export_cell(log.ad_title),
        export_cell(STATUS_LABELS.get(log.status, log.status)),
        export_cell(log.error_message),
        export_cell(log.task_id),
    ]


# --- Повтор отправки ----------------------------------------------------------
#
# HIST-04. Единственное настоящее ДЕЙСТВИЕ раздела: всё остальное здесь читает.
# Путь ведёт прямо в боевую очередь, отправка в стороннюю группу не отзывается и
# тратит баланс, поэтому КАЖДАЯ проверка ниже стоит ДО постановки в очередь.

# Имя Celery-таска повтора (заведён планом 04-03). Постановка идёт ПО ИМЕНИ:
# импорт самого таска в web-слой затащил бы сюда модуль воркера целиком вместе
# с его зависимостями.
RETRY_TASK_NAME = "app.worker.tasks.retry_send"

# Признаки исхода повтора, приезжающие на список перенаправлением. Значение
# сравнивается ЦЕЛИКОМ по этому словарю — тем же приёмом, что признак
# несостоявшейся выгрузки: плашка по любому непустому содержимому параметра
# позволяла бы чужой ссылкой нарисовать пользователю сообщение о событии,
# которого не было.
RETRY_QUEUED = "queued"
RETRY_GONE = "gone"
RETRY_NO_BALANCE = "no_balance"
RETRY_BUSY = "busy"

# Тексты ПОСТОЯННЫЕ и из ответа гейта баланса не собираются. Гейт возвращает
# причину строкой, и провоз этой строки через адрес означал бы, что владелец
# ссылки печатает пользователю произвольный текст на его собственной странице.
RETRY_NOTICES = {
    RETRY_QUEUED: (
        "Повтор поставлен в очередь. Уйдёт ТЕКУЩЕЕ содержимое объявления, "
        "а не то, что показано в записи.",
        "success",
    ),
    RETRY_GONE: (
        "Повторить не удалось: объявления, группы или аккаунта этой отправки "
        "больше нет либо аккаунт отключён.",
        "warning",
    ),
    RETRY_NO_BALANCE: (
        "Повторить не удалось: баланс сообщений исчерпан. Пополните баланс — "
        "и повтор станет доступен.",
        "warning",
    ),
    RETRY_BUSY: (
        "Повтор этой отправки уже выполняется — второй раз он не уйдёт.",
        "info",
    ),
}


def _is_same_origin(request: Request) -> bool:
    """Пришёл ли изменяющий запрос со страницы САМОГО приложения (T-04-38).

    ЗАЧЕМ. Аутентификация проекта идёт cookie, а действие повтора необратимо:
    отправка в стороннюю группу не отзывается и тратит баланс. Именно эта фаза
    ВВОДИТ форму, запускающую такое действие, и ASVS L1 (V4.2.2) требует защиты
    изменяющих состояние запросов от межсайтовой подделки. Сверка заголовков —
    единственный вариант, который не требует ни схемы токенов на весь проект,
    ни правки шаблонов, ни новой зависимости.

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

    ⚠️ РАМКИ. Проверка живёт в обработчике повтора и только в нём. Остальные
    формы проекта (удаления через POST) защиты не получают — фаза не расширяет
    рамки; остаток вынесен в отчёт безопасности фазы отдельной рекомендацией.
    """
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site:
        return fetch_site == "same-origin"
    origin = request.headers.get("origin")
    if origin:
        return urlsplit(origin).hostname == request.url.hostname
    return True


# Записи журнала, повтор которых ставится в очередь прямо сейчас в ЭТОМ
# процессе. Реестр — в памяти, а не в БД, по образцу реестра синхронизации
# аккаунтов (`app/pages/accounts.py`).
#
# ⚠️ ГРАНИЦА ПРИЁМА, НАЗВАННАЯ ЯВНО. Реестр живёт в памяти ОДНОГО рабочего
# процесса и нескольких процессов не переживает: два одновременных нажатия,
# попавшие в разные процессы, обе заявки займут успешно. Ограничение уже
# принято проектом для синхронизации, но здесь цена ошибки выше — вторая
# необратимая отправка в чужую группу. Поэтому оно записано и здесь, и в отчёте
# безопасности фазы, а не умолчано. Остальные три линии защиты от двойной
# отправки (перенаправление после формы, гард панели подтверждения, отсутствие
# автоперезапуска у самого таска) от числа процессов не зависят.
_RETRY_IN_FLIGHT: set[int] = set()


def _claim_retry_slot(log_id: int) -> bool:
    """Занимает заявку на повтор записи. `False` — заявка уже занята.

    Функция СИНХРОННАЯ и не содержит ни одного `await` намеренно: между
    проверкой и добавлением не должно быть точки переключения задач, иначе
    гонка вернётся ровно туда, откуда её убирают.
    """
    if log_id in _RETRY_IN_FLIGHT:
        return False
    _RETRY_IN_FLIGHT.add(log_id)
    return True


def _release_retry_slot(log_id: int) -> None:
    """Освобождает заявку. К БД не обращается и отказать не может.

    Вызывается из блока завершения — в том числе после исключения, когда
    сессия непригодна ни для чего, кроме отката. Отбрасывание, а не удаление:
    повторный вызов обязан быть безобидным.
    """
    _RETRY_IN_FLIGHT.discard(log_id)


@router.get("/history/partial", response_class=HTMLResponse)
async def history_partial(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    status = _clean_choice(status, STATUS_VALUES)
    messenger = _clean_choice(messenger, MESSENGER_VALUES)
    period = _clean_choice(period, PERIOD_VALUES)
    account_id_int = _parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > limit
    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "ad_images": r.ad_images or [],
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in rows[:limit]
    ]
    filter_params = history_filter_params(status, messenger, account_id_int, period)
    return templates.TemplateResponse(
        "history/partial_cards.html",
        {
            "request": request,
            "user": user,
            "logs": logs,
            "has_next": has_next,
            "next_offset": offset + limit,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
        },
    )


@router.get("/history/export")
async def history_export(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Потоковая выгрузка ОТФИЛЬТРОВАННОЙ истории файлом (HIST-03).

    ОБЪЯВЛЕН ВЫШЕ МАРШРУТА ЗАПИСИ. Сопоставление идёт в порядке объявления, и
    объявленный ниже адрес уехал бы в `log_id` маршрута записи, отдав ошибку
    разбора вместо файла. Ровно по этой причине выше маршрута записи уже стоит
    паршал бесконечной прокрутки.

    ФИЛЬТРЫ — ТЕ ЖЕ, ЧТО У СПИСКА, И НАВЕШИВАЕТ ИХ ТА ЖЕ ФУНКЦИЯ. Иначе
    обещание «выгружено именно то, что показано» перестало бы быть проверяемым
    утверждением: две копии условий расходятся молча, и пользователь уносит
    файл, не совпадающий с экраном. Отсечка `_clean_choice` стоит и здесь —
    выгрузка ТРЕТИЙ вход на те же оси, и без неё подобранное вручную значение
    отдавало бы пустой файл, неотличимый от «записей действительно нет».

    ВНЕШНЕЕ СОЕДИНЕНИЕ С ГРУППОЙ ОБЯЗАТЕЛЬНО даже без фильтра по аккаунту:
    условие по `Group.account_id` иначе не с чем связать, и фильтр развалился
    бы молча. Записей соединение не теряет — отправка с удалённой группой
    остаётся в файле.

    ⚠️ НЕСУЩЕЕ ОГРАНИЧЕНИЕ. Корректность держится на том, что генераторные
    зависимости (сессия БД из `get_db`) закрываются ПОСЛЕ отправки тела ответа;
    требование `fastapi>=0.129.0` записано в `pyproject.toml` и ослаблению не
    подлежит. Суита эту границу не проверяет вовсе: подмена `get_db` в тестах
    генератором не является, и времени закрытия сессии в тестах не наблюдается.
    Пункт вынесен в ручные проверки плана 04-10.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    status = _clean_choice(status, STATUS_VALUES)
    messenger = _clean_choice(messenger, MESSENGER_VALUES)
    period = _clean_choice(period, PERIOD_VALUES)
    account_id_int = _parse_account_id(account_id)

    # ПОТОЛОК ПРОВЕРЯЕТСЯ ДО КОНСТРУИРОВАНИЯ ПОТОКА (D-27, T-04-33). У потокового
    # ответа код и заголовки уходят до первого фрагмента тела и после уже
    # неизменяемы: проверка внутри генератора дала бы либо файл со статусом
    # успеха и текстом ошибки внутри, либо обрезанный файл без единого признака
    # обрезки. Число считает тот же счётчик, что показывает линейка над
    # списком, — вызов один, потребителя два, и разойтись им не на чем.
    total = await history_count(
        db,
        user_id=user.id,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )
    if total > EXPORT_ROW_CAP:
        # Перенаправление на ТОТ ЖЕ отфильтрованный список: потерянные здесь
        # фильтры показали бы другой экран и предложили бы сузить период у
        # выборки, которую пользователь не выгружал.
        params = history_filter_params(status, messenger, account_id_int, period)
        params["export"] = EXPORT_TOO_MANY
        return RedirectResponse(url=f"/history?{urlencode(params)}", status_code=302)

    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )
    query = query.order_by(SendLog.sent_at.desc()).execution_options(
        yield_per=EXPORT_YIELD_PER
    )

    async def body():
        """Метка порядка байтов, шапка, затем строки — партиями.

        Запись идёт стандартным модулем CSV в буфер на одну строку: он ставит
        кавычки там, где значение содержит разделитель, кавычку или перевод
        строки, — руками этот набор случаев не выписывается без ошибок.
        """
        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter=EXPORT_DELIMITER,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\r\n",
        )

        def flush() -> str:
            chunk = buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            return chunk

        writer.writerow(EXPORT_HEADER)
        # Метка порядка байтов — ПЕРВЫЕ байты тела (D-25). Без неё табличный
        # редактор в русской локали читает файл однобайтовой кодировкой, и
        # кириллица приезжает мусором: файл открывается, выглядит заполненным и
        # не содержит ни одного читаемого слова.
        yield EXPORT_BOM + flush()

        # Чтение ПОТОКОМ, а не одной выборкой: память держится порядка размера
        # партии, а не размера выборки (T-04-32). На боевом драйвере это
        # серверный курсор, на тестовом — буферизация партиями; интерфейс один.
        result = await db.stream(query)
        async for log, group in result:
            writer.writerow(export_row(log, group, user))
            yield flush()

    return StreamingResponse(
        body(),
        media_type="text/csv; charset=utf-8",
        # Имя файла — константа модуля и из значений пользователя не собирается
        # (T-04-34): подстановка в заголовок ответа невозможна по построению.
        headers={
            "Content-Disposition": f'attachment; filename="{EXPORT_FILENAME}"',
        },
    )


@router.get("/history/{log_id}", response_class=HTMLResponse)
async def history_detail(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user.id:
        return RedirectResponse(url="/history", status_code=302)

    group = await db.get(Group, log.group_id) if log.group_id else None

    return templates.TemplateResponse(
        "history/detail.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "log": log,
            "group": group,
            "active_page": "history",
        },
    )


@router.post("/history/{log_id}/retry")
async def history_retry(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Ставит повтор отправки в очередь (HIST-04).

    ПОРЯДОК ПРОВЕРОК — ЧАСТЬ КОНТРАКТА, а не оформление. Каждая стоит ДО
    постановки в очередь, потому что отправка необратима: проверка, сделанная
    внутри самой отправки, означала бы запись в журнал о заведомо невозможной
    отправке, а то и настоящее сообщение в чужую группу.

    1. Гард входа.
    2. Сверка источника запроса — ПЕРВОЕ, что делается после гарда, до чтения
       чего бы то ни было: подделанный межсайтовый запрос не имеет права
       вызвать ни одного побочного эффекта. Отказ — код 403 без
       перенаправления: дружелюбный ответ ему не полагается, а однозначный код
       делает тест недвусмысленным.
    3. Владение. Клиентским данным не верят: идентификатор приезжает из адреса.
    4. Пригодность. Повторяется НЕуспешная запись, и предикат — «статус не
       успешный», а не «статус из перечня известных неудач». Перечень конечен
       ровно до появления следующего статуса, и запись с неизвестным значением
       оказалась бы ни успешной, ни повторяемой — тот же предикат держат
       счётчик неудач дашборда и кнопка копирования диагностики.
    5. Предпроверка целости тройки (D-21): объявление, группа и аккаунт через
       группу, плюс активность аккаунта. Случай реальный — удалённая группа
       возвращается синхронизацией НОВОЙ строкой с новым идентификатором, и
       ссылка старой записи ведёт в никуда.
    6. Гейт баланса (T-04-36). Он стоит у планировщика, а не внутри отправки;
       без этого шага повтор стал бы способом отправить столько, сколько у
       пользователя неудачных записей, в обход тарифного лимита. Биллинг здесь
       не правится: списание за успешный повтор произойдёт там же, где у боевой
       рассылки (D-20).

    ЗАЯВКА ЗАНИМАЕТСЯ ДО ЛЮБОЙ АСИНХРОННОЙ РАБОТЫ по записи и освобождается в
    блоке завершения — второе нажатие в пределах процесса второй задачи не
    ставит.

    ОТВЕТ — ПЕРЕНАПРАВЛЕНИЕ. Оно же закрывает повтор по обновлению страницы и
    по кнопке возврата браузера.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if not _is_same_origin(request):
        return Response(status_code=403)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user.id:
        return RedirectResponse(url="/history", status_code=302)

    if log.status == STATUS_OK:
        return RedirectResponse(url="/history", status_code=302)

    if not _claim_retry_slot(log.id):
        return RedirectResponse(url=f"/history?retry={RETRY_BUSY}", status_code=302)

    try:
        group = await db.get(Group, log.group_id) if log.group_id else None
        ad = await db.get(Ad, log.ad_id) if log.ad_id else None
        # У журнала колонки аккаунта нет вовсе — аккаунт выводится через группу.
        account = (
            await db.get(MessengerAccount, group.account_id)
            if group and group.account_id
            else None
        )
        if not ad or not group or not account or account.status != "active":
            return RedirectResponse(
                url=f"/history?retry={RETRY_GONE}", status_code=302
            )

        allowed, _reason = await check_balance_cached(db, user.id, "send")
        if not allowed:
            return RedirectResponse(
                url=f"/history?retry={RETRY_NO_BALANCE}", status_code=302
            )

        # Импорт ЛОКАЛЬНЫЙ и обязан таким остаться: именно он позволяет
        # подменить модуль очереди в тесте. Поднятый на уровень модуля, он
        # разрешился бы один раз при загрузке пакета страниц, и любой тест
        # повтора пошёл бы к настоящему брокеру.
        from app.worker.celery_app import celery

        celery.send_task(RETRY_TASK_NAME, args=[log.id, user.id])
    finally:
        _release_retry_slot(log.id)

    return RedirectResponse(url=f"/history?retry={RETRY_QUEUED}", status_code=302)


@router.get("/history", response_class=HTMLResponse)
async def history_list(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    export: str | None = Query(default=None),
    retry: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    status = _clean_choice(status, STATUS_VALUES)
    messenger = _clean_choice(messenger, MESSENGER_VALUES)
    period = _clean_choice(period, PERIOD_VALUES)
    account_id_int = _parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(PAGE_SIZE + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > PAGE_SIZE
    rows = rows[:PAGE_SIZE]

    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "ad_images": r.ad_images or [],
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in rows
    ]

    accounts_result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.user_id == user.id)
    )
    all_accounts = accounts_result.scalars().all()
    filter_params = history_filter_params(status, messenger, account_id_int, period)

    # Точное число найденного ОТДЕЛЬНЫМ запросом с тем же набором фильтров
    # (D-31) — тот же приём, что у счётчиков на экране групп аккаунта.
    # Считать по длине выданного списка нельзя: список ограничен страницей, и
    # такое число было бы верным ровно до тридцать первой записи, после чего
    # молча врало бы — причём именно там, где счётчик и нужен. Число это
    # обещание, на которое обопрётся выгрузка (план 04-08): выгрузка и счётчик
    # обязаны отвечать одним числом на один вопрос, поэтому фильтры в обоих
    # навешивает одна и та же функция модуля аналитики.
    #
    # В паршале прокрутки счётчик НЕ пересчитывается: он живёт над списком, а
    # паршал подменяет только порцию записей и линейки не касается.
    history_total = await history_count(
        db,
        user_id=user.id,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "logs": logs,
            "all_accounts": all_accounts,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            # Наборы значений уходят ТОЛЬКО в список: чипсы живут над выдачей и
            # подменой порций прокрутки не затрагиваются. Паршал получает
            # активные значения (они едут в адресе сентинеля) и не получает
            # перечней, которых не рисует.
            "status_chips": STATUS_CHIPS,
            "messenger_chips": MESSENGER_CHIPS,
            "period_chips": PERIOD_CHIPS,
            "history_total": history_total,
            # Признак несостоявшейся выгрузки сравнивается ЦЕЛИКОМ, как и
            # значения осей фильтрации: плашка по любому непустому значению
            # позволяла бы чужой ссылкой нарисовать пользователю сообщение о
            # выгрузке, которой не было.
            "export_blocked": export == EXPORT_TOO_MANY,
            "export_row_cap": EXPORT_ROW_CAP,
            # Исход повтора приезжает признаком в адресе и разбирается ПО
            # СЛОВАРЮ известных значений: неизвестное содержимое параметра не
            # рисует ничего. Иначе чужая ссылка печатала бы пользователю
            # сообщение о повторе, которого не было.
            "retry_notice": RETRY_NOTICES.get(retry),
            "offset": offset,
            "page_size": PAGE_SIZE,
            "has_next": has_next,
            "next_offset": offset + len(logs),
            "active_page": "history",
        },
    )
