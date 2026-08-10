import re

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30

# Список ключей вложений приходит скрытыми полями формы (и телом JSON на
# API-входе) и полностью управляем клиентом: он ключ ОБЪЯВЛЯЕТ, но не доказывает
# ни его формы, ни принадлежности отправителю. Без проверки объявление
# сохраняется с ключом из чужого префикса того же хранилища, и чужое изображение
# начинает отдаваться в карточке, истории и админке (WR-01 / T-10-04).
#
# Форма ключа — источник правды `app/routes/uploads.py`: `{user_id}/{32 hex}_{имя}`,
# где `uuid4().hex` даёт ровно 32 шестнадцатеричных символа, а `safe_filename`
# сводит имя к `[A-Za-z0-9._-]` длиной до 100.
_IMAGE_KEY_PATTERN = re.compile(r"^(\d+)/[0-9a-f]{32}_[A-Za-z0-9._-]{1,100}$")

INACCESSIBLE_IMAGE_MESSAGE = (
    "Одно из вложений недоступно. Обновите страницу и добавьте изображение заново."
)


def own_image_keys(values: list[str], user_id: int, max_images: int) -> list[str]:
    """Проверить, что каждый ключ вложения принадлежит вызывающему.

    Возвращает список в исходном порядке загрузки. Поднимает ``HTTPException``
    с кодом 400, если значение не соответствует форме ключа, лежит вне префикса
    вызывающего или если вложений больше ``max_images``.

    Отказ, а не молчаливое отбрасывание значения: отбрасывание превратило бы
    попытку подмены в «успешное сохранение без картинки» и скрыло бы её от
    пользователя, оставив в БД тихо расходящееся с формой состояние.

    Отказ оформлен ``HTTPException`` на обоих слоях сознательно. Страничный слой
    в этом проекте отвечает редиректами, но редирект здесь означал бы потерю
    данных без объяснения: пользователь увидел бы список объявлений и не узнал,
    что сохранение не состоялось. Ошибка по данным — не навигация.
    """
    if len(values) > max_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Объявление не сохранено: вложений больше {max_images}. "
                "Удалите лишние и нажмите «Сохранить»."
            ),
        )

    for value in values:
        match = _IMAGE_KEY_PATTERN.match(value)
        if match is None or int(match.group(1)) != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=INACCESSIBLE_IMAGE_MESSAGE,
            )

    return list(values)


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


@router.get("/ads/new", response_class=HTMLResponse)
async def ads_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "is_admin": check_is_admin(user, settings), "ad": None, "active_page": "ads"},
    )


@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form_data = await request.form()
    image_list = own_image_keys(
        [v for v in form_data.getlist("images") if v.strip()],
        user.id,
        settings.max_images_per_ad,
    )
    ad = Ad(user_id=user.id, title=title, text=text, images=image_list)
    db.add(ad)
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_edit(
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
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "is_admin": check_is_admin(user, settings), "ad": ad, "active_page": "ads"},
    )


@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
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

    form_data = await request.form()
    # Проверка до первой записи в модель: иначе отказ оставил бы объявление
    # частично изменённым (заголовок новый, вложения старые).
    image_list = own_image_keys(
        [v for v in form_data.getlist("images") if v.strip()],
        user.id,
        settings.max_images_per_ad,
    )
    ad.title = title
    ad.text = text
    ad.images = image_list
    ad.is_active = is_active
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


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
