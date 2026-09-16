from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED, AD_STATUSES
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.pages.common import (
    check_is_admin,
    get_user_from_cookie,
    is_same_origin,
    templates,
)
# `respond` ввозится ТОЙ ЖЕ строкой, что и признак: второе объявление ввоза из
# слоя ответа в одном модуле было бы вторым местом, куда смотрят, решая форму
# ответа, — а решение здесь одно и приходит из одного места (план 10-03).
from app.pages.htmx import is_htmx, respond
# ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА ВВОЗИТСЯ, А НЕ ПОВТОРЯЕТСЯ ЗДЕСЬ ЧИСЛОМ.
# Величина есть свойство КОЛОНКИ, общее всем таблицам проекта, и живёт она в
# одном месте — `app/pages/identifiers.py`. Вторая копия числа в этом файле
# разошлась бы с первой молча при первой же правке колонки (`CR-01` пятого
# круга ревизии — ровно тот класс отказа, который фаза закрывает).
from app.pages.identifiers import ID_MAX, IdPath
# Форма ключа вложения и правило владения им живут в НЕЙТРАЛЬНОМ модуле: от него
# зависят оба слоя, а он — ни от одного из них (WR-04). Прежние имена остаются
# доступными здесь, поэтому точки вызова в этом файле не переписываются.
from app.services.image_keys import INACCESSIBLE_IMAGE_MESSAGE, own_image_keys

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30

# Предел длины текста и порог предупреждения счётчика (UI-SPEC E1 `overflow`).
# Ограничения длины в коде проекта нет: `Ad.text` — Text без длины, все три
# адаптера передают текст как есть. Пороги — внешний факт о Telegram: 4096
# символов обычного текста и 1024 символа подписи к медиа для не-Premium
# аккаунта. Premium-статус подключённого userbot-аккаунта приложению неизвестен,
# поэтому счётчик ПРЕДУПРЕЖДАЕТ, но сохранение НЕ блокирует: протоколы отправки
# эта фаза не трогает, а обрезать текст на сохранении нельзя.
TEXT_LIMIT = 4096
TEXT_WARN_RATIO = 0.9
# При непустом списке вложений текст уходит подписью к медиа, и выше этого
# порога отправка в Telegram без Premium гарантированно упадёт
# MediaCaptionTooLongError — сегодня эта ошибка молча легла бы в SendLog.
CAPTION_LIMIT = 1024

# Подписи каналов для предпросмотра. Источник тех же слов —
# app/templates/includes/messenger_icon.html; сюда они приходят потому, что
# предпросмотр называет канал ТЕКСТОМ, а не иконкой (D-11: вид единый).
MESSENGER_LABELS = {"tg_user": "Telegram", "wa": "WhatsApp", "max": "MAX"}

# Порядок пилюль каналов на карточке списка. Перечень ЗАКРЫТЫЙ и по нему же
# отбираются известные типы: у расписания с удалённым аккаунтом (issue #35)
# типа нет вовсе, а ветка неизвестного типа в messenger_icon отдаёт
# .msg--plain — тон пилюли ей не достаётся, и на карточке появилась бы
# бесцветная надпись «None». Порядок объявлен явно, чтобы две карточки с одним
# набором каналов не показывали их в разной последовательности: группировка в
# БД порядка строк не обещает.
CHANNEL_ORDER = ("tg_user", "wa", "max")

# Один текст на два случая — «нет такой записи» и «запись чужая» (T-02G-02).
# Разные тексты подтвердили бы существование чужого объявления по одному лишь
# перебору идентификаторов.
INACCESSIBLE_AD_MESSAGE = "Объявление недоступно. Обновите страницу и попробуйте снова."

# ⚠️ ТЕКСТА И ПЕРЕЧНЯ ПРИЗНАКОВ ОТКАЗА РАСПИСАНИЯ ЗДЕСЬ БОЛЬШЕ НЕТ. Требование
# UI-SPEC (E4 `error`) в силе: редактор обязан СКАЗАТЬ, почему сохранение не
# состоялось. Изменился владелец слов — формулировка переехала посимвольно в
# закрытый реестр `app/pages/notices.py`, где ей отвечают ДВА кода
# (`schedule_account_gone` и `schedule_ad_missing`) с одним и тем же текстом:
# различать эти случаи нужно ЖУРНАЛУ, а человеку на экране нельзя — разные
# слова подтвердили бы существование чужой записи одним перебором
# идентификаторов. Довод «в разметку уходит серверная строка, а признак только
# ВЫБИРАЕТ её» никуда не делся: он стал свойством реестра.


async def _enrich_ads_with_stats(db: AsyncSession, ads: list[Ad]) -> None:
    """Добавляет sends_count, schedules_count и channels к каждому объявлению."""
    if not ads:
        return
    ad_ids = [a.id for a in ads]
    # Успешные отправки по ad_id
    sends_result = await db.execute(
        select(SendLog.ad_id, func.count().label("cnt"))
        .where(SendLog.ad_id.in_(ad_ids), SendLog.status == "ok")
        .group_by(SendLog.ad_id)
    )
    sends_map = {r.ad_id: r.cnt for r in sends_result.all()}
    # Расписания по ad_id
    sched_result = await db.execute(
        select(Schedule.ad_id, func.count().label("cnt"))
        .where(Schedule.ad_id.in_(ad_ids))
        .group_by(Schedule.ad_id)
    )
    sched_map = {r.ad_id: r.cnt for r in sched_result.all()}
    # Каналы по ad_id — ТРЕТИЙ сгруппированный запрос на страницу выдачи, по
    # форме двух соседних (T-m0b-05). Запрос НА ОБЪЯВЛЕНИЕ в цикле здесь
    # заводить нельзя: страница отдаёт до PAGE_SIZE карточек, и цикл превратил
    # бы один показ списка в тридцать обращений к БД.
    # outer join: расписание с удалённым аккаунтом (issue #35) обязано остаться
    # в счёте расписаний соседнего запроса и просто не дать канала здесь —
    # внутреннее соединение молча выкинуло бы его строку.
    chan_result = await db.execute(
        select(Schedule.ad_id, MessengerAccount.type, func.count().label("cnt"))
        .join(
            MessengerAccount, Schedule.account_id == MessengerAccount.id, isouter=True
        )
        .where(Schedule.ad_id.in_(ad_ids))
        .group_by(Schedule.ad_id, MessengerAccount.type)
    )
    chan_map: dict[int, dict[str, int]] = {}
    for row in chan_result.all():
        if row.type not in CHANNEL_ORDER:
            continue
        chan_map.setdefault(row.ad_id, {})[row.type] = row.cnt
    for ad in ads:
        ad.sends_count = sends_map.get(ad.id, 0) or 0
        ad.schedules_count = sched_map.get(ad.id, 0) or 0
        # ПУСТОЙ СПИСОК, а не отсутствие поля: неизвестное имя Jinja печатает
        # пустотой, и опечатка в шаблоне выглядела бы как «у объявления нет
        # каналов», а не как ошибка.
        counts = chan_map.get(ad.id, {})
        ad.channels = [(t, counts[t]) for t in CHANNEL_ORDER if t in counts]


def _ads_filter_params(search: str) -> dict:
    """Действующий отбор для URL сентинела бесконечной прокрутки.

    Потерянный здесь отбор не роняет страницу — он молча подмешивает
    неотобранные объявления к отобранным на второй странице выдачи.
    """
    params = {}
    if search:
        params["search"] = search
    return params


def _ads_conditions(user_id: int, search: str) -> list:
    """ОДНО условие отбора на выдачу и на счёт.

    Разъехавшись, счётчик показывал бы одно число, а сетка — другой набор
    карточек. Владение стоит ПЕРВЫМ слагаемым и не заменяется поиском ни в
    одной ветке (T-m0b-01): счёт, посчитанный шире выдачи, назвал бы
    пользователю число чужих записей (T-m0b-03).

    Поиск идёт по названию ИЛИ по тексту — макет обещает обе оси одним полем
    (unpacked.html:471). Условие строится выражениями SQLAlchemy: строковой
    сборки запроса здесь нет ни в одной ветке (T-m0b-02).
    """
    conditions = [Ad.user_id == user_id]
    if search:
        pattern = f"%{search}%"
        conditions.append(or_(Ad.title.ilike(pattern), Ad.text.ilike(pattern)))
    return conditions


@router.get("/ads/partial", response_class=HTMLResponse)
async def ads_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    search: str | None = Query(None),
    # D-15: параметр компоновки принимается и игнорируется. Строчная вёрстка
    # удалена как недостижимая, но у пользователей есть открытые вкладки, чьи
    # сентинелы всё ещё несут этот параметр в URL — удаление его из сигнатуры
    # превратило бы их подгрузку в ошибку валидации.
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    # Пустая и состоящая из пробелов строка означают «отбора нет»: `?search=`
    # и отсутствие ключа обязаны значить одно и то же — то же правило, что
    # записано в components/filter_chips.html.
    search = (search or "").strip()
    result = await db.execute(
        select(Ad)
        .where(*_ads_conditions(user.id, search))
        .order_by(Ad.created_at.desc())
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    ads = rows[:limit]
    await _enrich_ads_with_stats(db, ads)
    return templates.TemplateResponse(
        "ads/partial_cards.html",
        {
            "request": request,
            "user": user,
            "ads": ads,
            "has_next": has_next,
            "next_offset": offset + limit,
            "filter_params": _ads_filter_params(search),
        },
    )


@router.get("/ads", response_class=HTMLResponse)
async def ads_list(
    request: Request,
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    search = (search or "").strip()
    conditions = _ads_conditions(user.id, search)
    # Признак «отбор применён» различает ДВА пустых состояния: «объявлений нет
    # вовсе» и «поиск ничего не нашёл» (UI-SPEC E13 `empty`). Второго запроса
    # для этого не нужно: сам отбор отвечает на вопрос.
    filters_active = bool(search)

    result = await db.execute(
        select(Ad)
        .where(*conditions)
        .order_by(Ad.created_at.desc())
        .limit(PAGE_SIZE + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    ads = rows[:PAGE_SIZE]
    await _enrich_ads_with_stats(db, ads)
    # Счёт — ОТДЕЛЬНЫЙ запрос по ТОМУ ЖЕ условию, а не длина отданной страницы:
    # страница ограничена PAGE_SIZE, и её длина соврала бы на любой выдаче
    # длиннее одной страницы, показав ровно размер страницы.
    total = (
        await db.execute(select(func.count()).select_from(Ad).where(*conditions))
    ).scalar_one()
    return templates.TemplateResponse(
        "ads/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "ads": ads,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "ads",
            "total": total,
            "filters_active": filters_active,
            "filter_search": search,
            "filter_params": _ads_filter_params(search),
        },
    )


async def _editor_context(
    db: AsyncSession,
    ad: Ad | None,
    settings: Settings,
    user=None,
    selected_schedule_id: int | None = None,
) -> dict:
    """Данные правой колонки редактора, секции расписаний и предпросмотра.

    Число расписаний, ближайший запуск и набор каналов, в которые объявление
    уйдёт по настроенным расписаниям (D-11 — вид единый, но подпись называет
    каналы честно), плюс всё, что нужно карточке расписания: сами расписания,
    аккаунты пользователя и его группы — активные, а к ним выключенные, уже
    выбранные в расписаниях этого объявления (D-07).

    Второго источника тех же чисел не заводится: план 02-05 ДОПОЛНЯЕТ эту
    функцию, а не пишет своё чтение рядом.
    """
    channels: list[str] = []
    schedules_count = 0
    next_run_at = None
    schedules: list[Schedule] = []

    if ad is not None:
        rows = (
            await db.execute(
                select(Schedule.next_run_at, MessengerAccount.type)
                .outerjoin(
                    MessengerAccount, Schedule.account_id == MessengerAccount.id
                )
                .where(Schedule.ad_id == ad.id)
            )
        ).all()
        schedules_count = len(rows)
        runs = [row.next_run_at for row in rows if row.next_run_at is not None]
        next_run_at = min(runs) if runs else None
        for row in rows:
            label = MESSENGER_LABELS.get(row.type)
            if label and label not in channels:
                channels.append(label)

        # Порядок карточек — порядок создания: перестановка расписаний между
        # перезагрузками сделала бы «ту же карточку» невозможно найти.
        schedules = list(
            (
                await db.execute(
                    select(Schedule)
                    .where(Schedule.ad_id == ad.id)
                    .order_by(Schedule.id)
                )
            )
            .scalars()
            .all()
        )

    # Идентификаторы групп, УЖЕ выбранных в расписаниях ИМЕННО ЭТОГО объявления
    # (D-07). Обход в Python, а не условием запроса: `Schedule.group_ids` — JSON-
    # список, и переносимого условия «идентификатор входит в JSON-массив» на
    # SQLite и PostgreSQL разом нет (образец обхода — подсчёт расписаний в
    # app/pages/groups.py). Расписания уже загружены выше — второго чтения не
    # добавляется.
    #
    # Множество строится ТОЛЬКО из расписаний этого объявления, а само оно
    # проверено на владение обработчиком выше. Значение внутри `group_ids`
    # подконтрольно отправителю формы, поэтому оно НЕ расширяет выборку само по
    # себе: условие владельца ниже остаётся обязательным (T-03-11).
    chosen_group_ids = {
        gid for schedule in schedules for gid in (schedule.group_ids or [])
    }

    accounts: list[MessengerAccount] = []
    groups: list[Group] = []
    inactive_group_ids: set[int] = set()
    if user is not None:
        accounts = list(
            (
                await db.execute(
                    select(MessengerAccount)
                    .where(MessengerAccount.user_id == user.id)
                    .order_by(MessengerAccount.id)
                )
            )
            .scalars()
            .all()
        )
        # Активные группы ПЛЮС выключенные, уже выбранные в расписаниях этого
        # объявления (D-07). С D-05 выключенная группа перестаёт получать
        # рассылку, и прежняя выборка «только активные» молча убирала выбранную
        # группу из карточки: пользователь не видел причину молчания группы, не
        # мог снять её выбор, а подпись «выбрано N из M» начинала врать
        # (RESEARCH Pitfall 6). Невыбранные выключенные в список по-прежнему не
        # попадают — иначе список выбора захламляется.
        #
        # При пустом множестве условие вырождается в прежнее «только активные»:
        # обычный случай обязан давать нулевой диф.
        group_scope = Group.is_active == True  # noqa: E712
        if chosen_group_ids:
            group_scope = group_scope | Group.id.in_(chosen_group_ids)
        groups = list(
            (
                await db.execute(
                    select(Group)
                    .where(Group.user_id == user.id, group_scope)
                    .order_by(Group.id)
                )
            )
            .scalars()
            .all()
        )
        # Признак выключенности едет в шаблон ОТДЕЛЬНЫМ множеством: карточке
        # нужна пометка, а второго запроса за флагом из разметки быть не может.
        inactive_group_ids = {g.id for g in groups if not g.is_active}

    # Развёрнута ОДНА карточка. Без выбора развёрнута только что добавленная —
    # её идентификатор приходит параметром запроса из редиректа обработчика
    # создания; при многих расписаниях это спасает от стены открытых форм
    # (UI-SPEC E7 zero-one-many).
    expanded_id = selected_schedule_id
    if expanded_id is not None and expanded_id not in {s.id for s in schedules}:
        expanded_id = None

    # Порог предупреждения счётчика зависит от НАЛИЧИЯ вложений, а не один на
    # все случаи: с вложениями текст уходит подписью к медиа, и его предел
    # существенно ниже. Один порог на оба случая либо пугал бы там, где всё в
    # порядке, либо молчал бы перед гарантированной ошибкой длины.
    has_images = bool(ad and ad.images)
    return {
        "channels": channels,
        "schedules_count": schedules_count,
        "next_run_at": next_run_at,
        "schedules": schedules,
        "accounts": accounts,
        "groups": groups,
        "inactive_group_ids": inactive_group_ids,
        "expanded_schedule_id": expanded_id,
        "text_limit": TEXT_LIMIT,
        "text_warn_at": CAPTION_LIMIT if has_images else int(TEXT_LIMIT * TEXT_WARN_RATIO),
        "caption_limit": CAPTION_LIMIT,
        "max_images": settings.max_images_per_ad,
    }


async def _autosave_response(
    request: Request,
    db: AsyncSession,
    settings: Settings,
    user,
    ad: Ad | None,
    error: str | None = None,
) -> HTMLResponse:
    """Внеполосный ответ автосохранения: предпросмотр, сводка и индикатор.

    Ключей администратора и активного раздела в контексте нет намеренно:
    фрагмент не перерисовывает оболочку страницы. Форма ответа скопирована с
    `app/pages/schedules.py::schedules_partial` — единственного фрагмент-маршрута
    проекта.
    """
    return templates.TemplateResponse(
        request,
        "ads/includes/autosave_response.html",
        {
            "user": user,
            "ad": ad,
            "editor": await _editor_context(db, ad, settings, user),
            "autosave_error": error,
        },
    )


def _attachment_refusal(
    request: Request,
    db: AsyncSession,
    settings: Settings,
    user,
    ad: Ad | None,
    exc: HTTPException,
):
    """ОТКАЗ ПО ВЛОЖЕНИЯМ — ЕДИНСТВЕННАЯ ВЕТКА РЕДАКТОРА ВНЕ СЛОЯ ОТВЕТА.

    ⚠️ ИЗЪЯТИЕ НАЗВАНО ЗДЕСЬ, А НЕ СПРЯТАНО, И ОСНОВАНИЕ У НЕГО ИЗМЕРЕНО. Слой
    ответа умеет ДВЕ формы для пути без JavaScript — перенаправление 302 — и
    третьей, отказа `400`, выразить не может: `respond()` принимает АДРЕС
    деградации, а не код. Между тем половина деградации этой ветки отвечает
    именно `400`, и это не догадка о прошлом, а действующий контракт, снятый
    восемью утверждениями суиты (`tests/test_pages/test_ads_image_ownership.py`
    — семь, `tests/test_pages/test_ads_editor.py` — одно; все отправлены БЕЗ
    признака htmx). Отправить эту ветку через слой ответа значило бы заменить
    отказ `400` перенаправлением `302`, то есть СМЕНИТЬ ПОВЕДЕНИЕ там, где план
    переезда обещал его сохранить.

    Поэтому решение о транспорте у этой ОДНОЙ ветки остаётся в приложении — и
    вынесено сюда, в отдельного помощника, чтобы оно было видно ИМЕНЕМ, а не
    пряталось строкой посреди пути сохранения. Три функции переезда
    (`_save_from_editor`, `ads_create`, `ads_update`) признака не читают вовсе.

    Половина htmx не меняется ни байтом: отказ остаётся В ИНДИКАТОРЕ (UI-SPEC E2
    `error`) — ни модального окна, ни общестраничного алерта, набранный текст не
    трогается, предпросмотр сохраняет последнее удачное состояние, потому что
    рендерится из базы, а не из отклонённого тела запроса.

    Возвращается та же пара, что и у удачного сохранения: адрес деградации и
    нульарный сборщик фрагмента. На пути без JavaScript пара не строится вовсе —
    исходное исключение поднимается дальше и доезжает до человека прежним `400`.
    """
    if not is_htmx(request):
        raise exc

    async def _refused() -> HTMLResponse:
        return await _autosave_response(
            request, db, settings, user, ad, error=str(exc.detail)
        )

    # Адрес деградации экрана редактора. На этой ветке он никуда не уезжает
    # (половина без JavaScript ушла исключением выше), но подаётся настоящим:
    # слой ответа проверяет его и на ветке фрагмента, и негодный адрес иначе
    # дожил бы в исходнике до дня, когда у ветки выключат фрагмент.
    return (f"/ads/{ad.id}/edit" if ad else "/ads/new"), _refused


async def _save_from_editor(
    request: Request,
    db: AsyncSession,
    settings: Settings,
    user,
    ad: Ad | None,
    title: str,
    text: str,
    status_value: str | None = None,
):
    """Один путь для автосохранения, «Сохранить» и работы без JavaScript.

    ⚠️ ПОКОЛЕНИЕ АБЗАЦА О ВЕТВЛЕНИИ (идиома D-30/D-32 — прежняя редакция не
    стирается). Здесь стояло: «ветвление — по наличию заголовка запроса htmx, а
    не по отдельным маршрутам». Утверждение было ВЕРНО для дерева, на котором
    писалось, и его СМЫСЛ — базовый путь D-09 обязан быть ТЕМ ЖЕ кодом, иначе он
    тихо разойдётся с улучшенным — не отменён, а УСИЛЕН: помощник больше не
    ветвится по транспорту ВООБЩЕ. Он делает работу и возвращает вызывающему
    ПАРУ — адрес деградации и нульарный async-сборщик фрагмента, — а какую из
    двух форм отдать человеку, решает слой ответа, один на проект (Фаза 11,
    план 11-06, D-02).

    Порядок шагов жёсткий: владение ключами вложений и лимит (план 02-02) →
    убирание вложения → запись и коммит → рендер предпросмотра из ПЕРЕЧИТАННОГО
    объекта. Пятый шаг не педантизм: сервер по D-13 отклоняет лишние вложения, а
    по WR-01 не принимает чужой ключ, и предпросмотр, собранный из тела запроса,
    показал бы то, чего в базе нет (ADS-06).

    ⚠️ СБОРЩИК СТРОИТ РАЗМЕТКУ ТОЛЬКО ТОГДА, КОГДА ОНА НУЖНА. Он нульарен и
    асинхронен, слой ответа делает `await fragment()`, и на пути без JavaScript
    выборки контекста редактора не выполняются вовсе.
    """
    created = ad is None
    form_data = await request.form()

    # Проверка ДО первой записи в модель: иначе отказ оставил бы объявление
    # частично изменённым (заголовок новый, вложения старые).
    raw_images = form_data.getlist("images")
    string_images = [value for value in raw_images if isinstance(value, str)]
    try:
        # Значение поля вложений обязано быть строкой. Многочастный запрос, в
        # котором `images` приходит ФАЙЛОВОЙ частью, даёт объект загруженного
        # файла, у которого строковой операции нет, и общий обработчик
        # превращает AttributeError в ответ 500 (WR-03). Соседняя `_clean_ints`
        # того же слоя уже защищается от этого класса ввода — защита приводится
        # к единому виду.
        #
        # Отказ, а не отбрасывание: молча выброшенная файловая часть сохранила
        # бы объявление БЕЗ вложений, то есть превратила бы кривой запрос в
        # «успешное сохранение без картинки». Ровно та причина, по которой
        # `own_image_keys` отказывает, а не отбрасывает.
        if len(string_images) != len(raw_images):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=INACCESSIBLE_IMAGE_MESSAGE,
            )
        image_list = own_image_keys(
            [v for v in string_images if v.strip()],
            user.id,
            settings.max_images_per_ad,
        )
    except HTTPException as exc:
        # Единственная ветка редактора, решающая транспорт сама, и решает его не
        # здесь, а в названном помощнике: половина деградации отвечает `400`, а
        # такой формы у слоя ответа нет (основание — докстринг помощника).
        return _attachment_refusal(request, db, settings, user, ad, exc)

    # D-12: убранное вложение исчезает из списка ключей объявления, но объект в
    # хранилище остаётся — снапшоты SendLog иначе превратились бы в битые
    # картинки. Убирается РОВНО одно вхождение, порядок остальных сохраняется:
    # порядок ключей — это порядок отправки.
    removed = form_data.get("remove_image")
    if removed and removed in image_list:
        image_list.remove(removed)

    if created:
        # D-03: запись появляется только здесь, первым сохранением. Заходом на
        # /ads/new пустых объявлений не создаётся.
        ad = Ad(
            user_id=user.id,
            title=title,
            text=text,
            images=image_list,
            status=AD_STATUS_DRAFT,
        )
        db.add(ad)
    else:
        ad.title = title
        ad.text = text
        ad.images = image_list

    # D-04: отдельной кнопки публикации в макете нет — публикует ЯВНОЕ нажатие
    # «Сохранить», которое приходит именованной кнопкой отправки. Эвристика
    # «текст непустой» опубликовала бы объявление, которое пользователь только
    # начал набирать, и планировщик разослал бы его по существующим расписаниям.
    # Автосохранение состояние не трогает вовсе.
    explicit_save = "save" in form_data
    if explicit_save:
        ad.status = AD_STATUS_PUBLISHED
    elif status_value in AD_STATUSES:
        # Значение вне словаря отбрасывается по той же причине, что и на
        # JSON-входе (T-02-11): произвольная строка не отфильтровалась бы ни как
        # черновик, ни как опубликованное.
        ad.status = status_value

    await db.commit()
    await db.refresh(ad)

    # Запись перечитана и дальше не меняется: сборщик держит ИМЕННО ЕЁ, а не
    # параметр `ad`, который выше был переприсвоен на ветке создания.
    saved = ad

    async def _fragment() -> HTMLResponse:
        """Ответ автосохранения: предпросмотр, сводка, индикатор, поле записи.

        ⚠️ ЗАГОЛОВОК ИСТОРИИ СТАВИТСЯ НА ТОТ ЖЕ ОБЪЕКТ, КОТОРЫЙ ФУНКЦИЯ
        ВОЗВРАЩАЕТ, И ЭТО НЕСУЩЕЕ СВОЙСТВО, А НЕ СТИЛЬ ЗАПИСИ. Он — единственное,
        что подменяет адрес в строке браузера после создания черновика: форма
        несёт неизменяемый `hx-post="/ads/new"`, и следующее автосохранение
        отличает обновление от создания только по скрытому полю, которое этот же
        ответ подменяет внеполосно. Ответ, собранный здесь, но не возвращённый
        отсюда, унёс бы заголовок с собой — и следующее автосохранение завело бы
        ВТОРОЙ черновик (D-03, D-13 Фазы 11).

        Значение собирается из `saved.id` ПЕРЕЧИТАННОЙ записи, а не из запроса:
        правый операнд записи заголовка не имеет права приходить от клиента
        (T-11-11, гейт G-13).
        """
        response = await _autosave_response(request, db, settings, user, saved)
        if created:
            response.headers["HX-Push-Url"] = f"/ads/{saved.id}/edit"
        return response

    # Адрес деградации. «Сохранить» завершает работу над объявлением и
    # возвращает в список; всё остальное (создание первым сохранением, убирание
    # вложения именованной кнопкой) оставляет пользователя в редакторе — иначе
    # убранное вложение выкидывало бы его со страницы. Ни одного собственного
    # перенаправления помощник больше не строит: он отдаёт АДРЕС, а ответ по
    # нему собирает слой.
    degraded = "/ads" if explicit_save else f"/ads/{saved.id}/edit"
    return degraded, _fragment


@router.get("/ads/new", response_class=HTMLResponse)
async def ads_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """D-03: открывает пустой редактор и НЕ создаёт запись."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "ads/form.html",
        {
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "ad": None,
            "editor": await _editor_context(db, None, settings, user),
            "active_page": "ads",
        },
    )


@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    # Поля необязательные: по D-03 черновик создаётся ПЕРВЫМ изменением, и на
    # этот момент второе поле почти всегда пустое. Признак required в разметке
    # тоже снят — htmx проверяет форму перед запросом и заблокировал бы первое
    # автосохранение вовсе.
    title: str = Form(""),
    text: str = Form(""),
    # Скрытое поле #ad-id-field: пустое до первого сохранения, дальше несёт
    # идентификатор созданного черновика, который ответ автосохранения подменил
    # внеполосно. Тип строковый, а не int: пустое значение приходит на КАЖДОМ
    # первом сохранении, и объявленный int дал бы 422 вместо создания записи.
    ad_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Создание черновика И его последующие автосохранения — один адрес.

    Форма несёт неизменяемый ``hx-post="/ads/new"`` и ``hx-swap="none"``: адрес
    следующего запроса не переписывается ничем, поэтому маршрутизация «создать
    или обновить» живёт ЗДЕСЬ, а не в браузере (CR-01). Клиентское переписывание
    ``hx-post`` оставило бы вторую строку ``ads`` создаваемой любым запросом в
    обход страницы — защита обязана быть серверной.

    ⚠️ СОБСТВЕННОГО ПЕРЕНАПРАВЛЕНИЯ У ОБРАБОТЧИКА НЕТ НИ В ОДНОЙ ВЕТКЕ (G-2), И
    ПРИЗНАКА htmx ОН НЕ ЧИТАЕТ (Фаза 11, план 11-06). Форму ответа выбирает слой
    письма, а ответ на обоих транспортах остаётся прежним ПОБАЙТОВО: с htmx —
    тот же внеполосный ответ автосохранения, без htmx — то же перенаправление на
    те же адреса. Переезд забирает у обработчика ВЫБОР формы, а не саму форму.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")

    # Путь СОЗДАНИЯ (D-03): поля нет, оно пустое или состоит из пробелов.
    if ad_id is None or not ad_id.strip():
        degraded, fragment = await _save_from_editor(
            request, db, settings, user, None, title=title, text=text
        )
        return await respond(request, redirect=degraded, fragment=fragment)

    # Владение подтверждается ОДНИМ запросом с обоими условиями — той же формой,
    # что применяет ads_update: «нет такой записи» и «запись чужая» обязаны
    # давать один исход, и ветку невозможно забыть (T-02G-01, T-02G-02).
    # Нечисловое значение неотличимо от несуществующего идентификатора.
    ad = None
    try:
        requested_id = int(ad_id)
    except ValueError:
        requested_id = None
    if requested_id is not None:
        ad = (
            await db.execute(
                select(Ad).where(Ad.id == requested_id, Ad.user_id == user.id)
            )
        ).scalar_one_or_none()

    # Отказ стоит ДО любой записи в модель: иначе неподтверждённый идентификатор
    # успевал бы изменить объект в сессии.
    if ad is None:

        async def _inaccessible() -> HTMLResponse:
            """Прежний ответ недоступного объявления, слово в слово.

            Несёт `ad=None`, то есть внеполосно ОБНУЛЯЕТ `#ad-id-field`:
            идентификатор, которым владеть не удалось, не должен уехать в
            следующий запрос ещё раз. Записи при этом не создаётся — иначе
            подстановка чужого идентификатора порождала бы черновики.
            """
            return await _autosave_response(
                request, db, settings, user, None, error=INACCESSIBLE_AD_MESSAGE
            )

        # Экран ОСТАЁТСЯ и лечится сам, поэтому исход фрагментный; адрес
        # деградации — прежний список, ровно тот, что уезжал отсюда 302.
        return await respond(request, redirect="/ads", fragment=_inaccessible)

    # Путь ОБНОВЛЕНИЯ. Помощник различает создание и обновление по аргументу
    # `ad` и ставит заголовок истории только при создании — на втором и
    # последующих запросах он не нужен, адрес в браузере уже верный.
    degraded, fragment = await _save_from_editor(
        request, db, settings, user, ad, title=title, text=text
    )
    return await respond(request, redirect=degraded, fragment=fragment)


@router.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_edit(
    request: Request,
    ad_id: IdPath,
    # Какая карточка расписания отрендерена развёрнутой. Это базовый путь
    # разворачивания без JavaScript (UI-SPEC §Interaction Contract): ссылка на
    # редактор с этим параметром, сервер рендерит указанную карточку
    # развёрнутой, остальные — свёрнутыми.
    #
    # ⚠️ ОБЕ ГРАНИЦЫ ДОБАВЛЕНЫ ПЛАНОМ 10-28, ПОТОМУ ЧТО НЕ БЫЛО НИ ОДНОЙ, И
    # ОСНОВАНИЕ У НИХ — ОБЪЯВЛЕННЫЙ ПРЕДМЕТ ПАРАМЕТРА, А НЕ ПРОСЛЕЖЕННЫЙ ПУТЬ.
    # Параметр объявлен ИДЕНТИФИКАТОРОМ РАСПИСАНИЯ, а идентификаторы этого
    # проекта лежат в диапазоне колонки (`app/models/schedule.py` — тот же
    # `Mapped[int]` без указания расширенной разрядности).
    #
    # ⚠️ РАЗНИЦА С КУРСОРОМ ПОСТРАНИЧНОГО ВЫВОДА ГРУПП НАЗВАНА ЗДЕСЬ, А НЕ
    # СГЛАЖЕНА. Курсор (`app/pages/account_groups.py`) ДОЕЗЖАЕТ до сравнения
    # по колонке (`Group.id > after_id`), и его граница есть граница колонки
    # по ПРОСЛЕЖЕННОМУ пути. Это значение до сравнения по колонке НЕ
    # ДОЕЗЖАЕТ: оно уходит в `_editor_context` под именем
    # `selected_schedule_id` и сличается там с УЖЕ ЗАГРУЖЕННЫМ составом
    # расписаний объявления в памяти (`expanded_id not in {s.id for s in
    # schedules}`), то есть операндом SQL не становится ни на одной ветке.
    # Закрыт он всё равно — по объявленному предмету, — и разница записана,
    # потому что молчаливое закрытие «на всякий случай» есть запись шире
    # дерева.
    #
    # ⚠️ ПУСТОЕ ЗНАЧЕНИЕ ОСТАЁТСЯ ЗАКОННЫМ СОСТОЯНИЕМ: расписание может быть
    # не выбрано, и это основной случай экрана, а не край. Граница ВЕЛИЧИНЫ к
    # ОТСУТСТВИЮ значения не применяется.
    sched: int | None = Query(None, ge=1, le=ID_MAX),
    # ⚠️ ПРИЗНАКА ОТКАЗА РАСПИСАНИЯ У ЭТОГО ОБРАБОТЧИКА БОЛЬШЕ НЕТ. Отказ по
    # данным при ПОДТВЕРЖДЁННО своём объявлении по-прежнему возвращает человека
    # сюда и по-прежнему обязан сказать, почему сохранение не состоялось
    # (WR-07), — но говорит это общая область уведомления шелла по коду
    # закрытого реестра, а не собственный параметр этой страницы.
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    return templates.TemplateResponse(
        request,
        "ads/form.html",
        {
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "ad": ad,
            "editor": await _editor_context(db, ad, settings, user, sched),
            "active_page": "ads",
        },
    )


@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: IdPath,
    title: str = Form(""),
    text: str = Form(""),
    # Имя параметра — НЕ `status`: модуль ответов FastAPI импортирован в этот
    # файл под тем же именем, и параметр формы затенял бы его на всё тело
    # функции. Любое будущее обращение к `status.HTTP_*` внутри обработчика
    # разрешалось бы тогда в присланную клиентом строку и падало бы
    # AttributeError на запросе, а не на импорте (WR-08). Имя НА ПРОВОДЕ
    # сохраняется алиасом: контракт формы не меняется.
    ad_status: str | None = Form(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Обновление по адресу маршрута. Поле `ad_id` из ТЕЛА здесь игнорируется.

    Форма редактора несёт скрытое `ad_id` на любом своём адресе, и параметра с
    таким именем в сигнатуре нет НАМЕРЕННО: адрес объявления тут задаёт путь
    маршрута, и тело не должно уметь перенаправить обновление на другую запись.
    Приняв его, обработчик получил бы второе определение «какую запись менять» —
    ровно та развилка, из-за которой разъехались два определения полноты
    расписания (WR-05).
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")
    # Владение внутри запроса, а не последующим `if`: «нет такой записи» и
    # «запись чужая» дают один исход, и ветку невозможно забыть (T-02-21).
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        # Оба транспорта приземляют на список: редактора несуществующего
        # объявления не бывает, и фрагменту некуда приехать. Адрес тот же, что
        # уезжал отсюда 302; вход из интерфейса недостижим — идентификатор пути
        # рисует сервер.
        return await respond(request, redirect="/ads")
    degraded, fragment = await _save_from_editor(
        request, db, settings, user, ad, title=title, text=text, status_value=ad_status
    )
    return await respond(request, redirect=degraded, fragment=fragment)


@router.post("/ads/{ad_id}/delete")
async def ads_delete(
    request: Request,
    ad_id: IdPath,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Удаление объявления. Необратимо.

    ⚠️ ОДИН МАРШРУТ ОБСЛУЖИВАЕТ ДВА МЕСТА ПОДТВЕРЖДЕНИЯ, И ЭТО ИЗМЕРЕНО, А НЕ
    предположено: карточка в списке объявлений и панель в редакторе объявления
    шлют один и тот же адрес. Оба уходят ОДНОЙ веткой перехода, и основания у
    них РАЗНЫЕ, хотя ответ один:

      * панель редактора принадлежала бы переходу и БЕЗ всякого изъятия —
        действие уводит с экрана, экрана после него нет;
      * карточка списка убирает строку с ОСТАЮЩЕГОСЯ экрана, то есть по классу
        действия принадлежала бы фрагментному пути, и в ветку перехода уходит по
        ОБЪЯВЛЕННОМУ ИЗЪЯТИЮ: обе копии разметки порции раздела просят следующую
        порцию СМЕЩЁННЫМ курсором, и фрагментное удаление сдвинуло бы список —
        следующая порция пропустила бы ровно одну карточку.

    Изъятие записано перечнем с обоснованием, фазой-снимателем и условием снятия
    (`OFFSET_CURSOR_EXCEPTIONS` в `tests/test_pages/test_htmx_gates.py`).
    Совпадение ответа у двух мест — следствие совпадения оснований, а не
    компромисс между ними.

    ⚠️ СОБСТВЕННОГО ОТВЕТА-ПЕРЕНАПРАВЛЕНИЯ ЗДЕСЬ НЕТ НИ В ОДНОЙ ВЕТКЕ, ВКЛЮЧАЯ
    «НЕТ СЕССИИ» (G-2). Ограничение владельца остаётся ВНУТРИ запроса: «нет
    такой записи» и «запись чужая» дают один исход, и ответ обоих неотличим от
    успешного.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")

    # СВЕРКА ИСТОЧНИКА (`WR-07`, ревизия 2026-09-04; прецедент — `CR-02` ревизии
    # Фазы 6). ГДЕ ОНА СТОИ́Т — сказано ОДИН РАЗ НА ПРОЕКТ, константой
    # `ORIGIN_CHECK_BOUNDARY` (`app/pages/common.py`, канон заведён планом
    # 10-25); текст канона здесь НЕ ПОВТОРЯЕТСЯ, площадка переведена на ССЫЛКУ
    # планом 10-32 (`WR-02`, ревизия 2026-09-07). Асимметрия закрыта решением, а
    # не совпадением: соседние административные маршруты несут эту же сверку, а
    # необратимое удаление данных пользователя не несло ничего, кроме умолчания
    # браузера, которого продукт не выставляет. Отказ по происхождению не имеет
    # права стать признаком существования строки.
    if not is_same_origin(request):
        return Response(status_code=403)

    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if ad:
        await db.delete(ad)
        await db.commit()
    return await respond(request, redirect="/ads")
