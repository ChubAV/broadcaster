from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED, AD_STATUSES
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates
# Форма ключа вложения и правило владения им живут в НЕЙТРАЛЬНОМ модуле: от него
# зависят оба слоя, а он — ни от одного из них (WR-04). Прежние имена остаются
# доступными здесь, поэтому точки вызова в этом файле не переписываются.
from app.services.image_keys import own_image_keys

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

# Один текст на два случая — «нет такой записи» и «запись чужая» (T-02G-02).
# Разные тексты подтвердили бы существование чужого объявления по одному лишь
# перебору идентификаторов.
INACCESSIBLE_AD_MESSAGE = "Объявление недоступно. Обновите страницу и попробуйте снова."

# Отказ обработчика расписания, о котором редактор обязан СКАЗАТЬ. Формулировка
# зафиксирована контрактом UI-SPEC (E4 `error`) и живёт ЗДЕСЬ, на сервере:
# в разметку попадает она, а не значение строки запроса. Значение подконтрольно
# отправителю — приняв его текстом, страница печатала бы произвольное сообщение
# от имени приложения по одной лишь ссылке с чужого сайта. Признак только
# ВЫБИРАЕТ текст; неизвестный признак не выбирает ничего.
SCHEDULE_ERROR_MESSAGE = (
    "Аккаунт или объявление недоступны. Обновите страницу и попробуйте снова."
)
SCHEDULE_ERROR_REASONS = ("account", "missing")


async def _enrich_ads_with_stats(db: AsyncSession, ads: list[Ad]) -> None:
    """Добавляет sends_count и schedules_count к каждому объявлению."""
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
    for ad in ads:
        ad.sends_count = sends_map.get(ad.id, 0) or 0
        ad.schedules_count = sched_map.get(ad.id, 0) or 0


@router.get("/ads/partial", response_class=HTMLResponse)
async def ads_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
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
    result = await db.execute(
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc()).offset(offset).limit(limit + 1)
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
        },
    )


@router.get("/ads", response_class=HTMLResponse)
async def ads_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc()).limit(PAGE_SIZE + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    ads = rows[:PAGE_SIZE]
    await _enrich_ads_with_stats(db, ads)
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
    аккаунты пользователя и его активные группы.

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

    accounts: list[MessengerAccount] = []
    groups: list[Group] = []
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
        groups = list(
            (
                await db.execute(
                    select(Group)
                    .where(Group.user_id == user.id, Group.is_active == True)  # noqa: E712
                    .order_by(Group.id)
                )
            )
            .scalars()
            .all()
        )

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

    Ветвление — по наличию заголовка запроса htmx, а не по отдельным маршрутам:
    базовый путь D-09 обязан быть ТЕМ ЖЕ кодом, иначе он тихо разойдётся с
    улучшенным.

    Порядок шагов жёсткий: владение ключами вложений и лимит (план 02-02) →
    убирание вложения → запись и коммит → рендер предпросмотра из ПЕРЕЧИТАННОГО
    объекта. Пятый шаг не педантизм: сервер по D-13 отклоняет лишние вложения, а
    по WR-01 не принимает чужой ключ, и предпросмотр, собранный из тела запроса,
    показал бы то, чего в базе нет (ADS-06).
    """
    is_htmx = request.headers.get("HX-Request") is not None
    created = ad is None
    form_data = await request.form()

    # Проверка ДО первой записи в модель: иначе отказ оставил бы объявление
    # частично изменённым (заголовок новый, вложения старые).
    try:
        image_list = own_image_keys(
            [v for v in form_data.getlist("images") if v.strip()],
            user.id,
            settings.max_images_per_ad,
        )
    except HTTPException as exc:
        if not is_htmx:
            raise
        # UI-SPEC E2 `error`: на htmx-пути отказ остаётся В ИНДИКАТОРЕ. Ни
        # модального окна, ни общестраничного алерта: набранный текст не
        # трогается, предпросмотр сохраняет последнее удачное состояние —
        # поэтому он рендерится из базы, а не из отклонённого тела запроса.
        return await _autosave_response(
            request, db, settings, user, ad, error=str(exc.detail)
        )

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

    if is_htmx:
        response = await _autosave_response(request, db, settings, user, ad)
        if created:
            # D-03: браузер подменяет адрес без перезагрузки — дальнейшие
            # автосохранения уходят уже на маршрут редактирования.
            response.headers["HX-Push-Url"] = f"/ads/{ad.id}/edit"
        return response

    # Путь без JavaScript. «Сохранить» завершает работу над объявлением и
    # возвращает в список; всё остальное (создание первым сохранением, убирание
    # вложения именованной кнопкой) оставляет пользователя в редакторе — иначе
    # убранное вложение выкидывало бы его со страницы.
    if explicit_save:
        return RedirectResponse(url="/ads", status_code=302)
    return RedirectResponse(url=f"/ads/{ad.id}/edit", status_code=302)


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
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Путь СОЗДАНИЯ (D-03): поля нет, оно пустое или состоит из пробелов.
    if ad_id is None or not ad_id.strip():
        return await _save_from_editor(
            request, db, settings, user, None, title=title, text=text
        )

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
        if request.headers.get("HX-Request") is not None:
            # Ответ несёт ad=None, то есть внеполосно ОБНУЛЯЕТ #ad-id-field:
            # идентификатор, которым владеть не удалось, не должен уехать в
            # следующий запрос ещё раз. Записи при этом не создаётся — иначе
            # подстановка чужого идентификатора порождала бы черновики.
            return await _autosave_response(
                request, db, settings, user, None, error=INACCESSIBLE_AD_MESSAGE
            )
        return RedirectResponse(url="/ads", status_code=302)

    # Путь ОБНОВЛЕНИЯ. _save_from_editor различает создание и обновление по
    # аргументу ad и ставит HX-Push-Url только при создании — на втором и
    # последующих запросах заголовок не нужен, адрес в браузере уже верный.
    return await _save_from_editor(
        request, db, settings, user, ad, title=title, text=text
    )


@router.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_edit(
    request: Request,
    ad_id: int,
    # Какая карточка расписания отрендерена развёрнутой. Это базовый путь
    # разворачивания без JavaScript (UI-SPEC §Interaction Contract): ссылка на
    # редактор с этим параметром, сервер рендерит указанную карточку
    # развёрнутой, остальные — свёрнутыми.
    sched: int | None = Query(None),
    # Признак отказа обработчика расписания (`app/pages/schedules.py`). Сюда
    # пользователя вернул отказ по данным при ПОДТВЕРЖДЁННО своём объявлении —
    # секция расписаний обязана сказать, почему сохранение не состоялось, а не
    # молча показать прежнее состояние (WR-07).
    sched_error: str | None = Query(None),
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
            # В шаблон уходит СЕРВЕРНЫЙ текст, выбранный признаком, а не сам
            # признак: неизвестное значение не выбирает ничего и сообщения не
            # рисует. Отказ страницы был бы здесь неверным исходом — значение
            # приходит строкой запроса, то есть из ссылки или закладки.
            "sched_error": (
                SCHEDULE_ERROR_MESSAGE
                if sched_error in SCHEDULE_ERROR_REASONS
                else None
            ),
        },
    )


@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(""),
    text: str = Form(""),
    status: str | None = Form(None),
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
        return RedirectResponse(url="/login", status_code=302)
    # Владение внутри запроса, а не последующим `if`: «нет такой записи» и
    # «запись чужая» дают один исход, и ветку невозможно забыть (T-02-21).
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    return await _save_from_editor(
        request, db, settings, user, ad, title=title, text=text, status_value=status
    )


@router.post("/ads/{ad_id}/delete")
async def ads_delete(
    request: Request,
    ad_id: int,
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
    if ad:
        await db.delete(ad)
        await db.commit()
    return RedirectResponse(url="/ads", status_code=302)
