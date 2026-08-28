from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import TIMEZONE_CHOICES, VALID_TIMEZONES
from app.dependencies import forbid_when_impersonating, get_db, get_settings
from app.pages import notices
from app.pages.common import check_is_admin, get_user_from_cookie, templates


router = APIRouter(tags=["pages"])


@router.get("/profile", response_class=HTMLResponse)
async def profile_get(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "profile",
            "timezone_choices": TIMEZONE_CHOICES,
        },
    )


@router.post("/profile")
async def profile_post(
    request: Request,
    timezone: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _under_another_identity: None = Depends(forbid_when_impersonating),
):
    """Правка учётных данных пользователя — ЗАПРЕЩЕНА ПОД ЧУЖОЙ ЛИЧНОСТЬЮ (D-22).

    ⚠️ ФОРМА ЗАКРЫТА ЦЕЛИКОМ, А НЕ ПОПОЛЬНО, И ЭТО РЕШЕНИЕ НА ВЫРОСТ. D-22
    называет смену адреса запрещённой, но ОТДЕЛЬНОГО маршрута смены адреса в
    продукте сегодня нет — когда его заведут, естественное место для него
    именно эта форма. Поле, добавленное в уже РАЗРЕШЁННЫЙ маршрут, машинный
    гейт запретов не заметил бы: маршрут-то объявлен, и полнота перечня по нему
    сходится. Запрет, поставленный заранее, снимает этот класс обхода целиком.

    ⚠️ ЧТЕНИЕ ПРОФИЛЯ ПРИ ЭТОМ ОТКРЫТО. Администратор под чужой личностью
    обязан ВИДЕТЬ настройки пользователя — часовой пояс объясняет, почему
    рассылка ушла не тогда, когда её ждали. Закрыт ровно изменяющий вход.

    Сегодняшнее содержимое формы — часовой пояс, и безобидным оно не является:
    им определяется, В КАКОЕ ВРЕМЯ уходят рассылки. Тихая правка часового пояса
    администратором сдвинула бы расписания пользователя, не оставив следа на
    экране, который тот открывает.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if timezone in VALID_TIMEZONES:
        user.timezone = timezone
        db.add(user)
        await db.commit()
        # ⚠️ ЭТОТ ИСХОД ВПЕРВЫЕ СТАНОВИТСЯ ВИДИМЫМ. Прежнее написание было
        # БУЛЕВЫМ признаком и не рисовалось НИ В ОДНОМ шаблоне продукта:
        # человек сохранял часовой пояс — то есть менял время, В КОТОРОЕ УХОДЯТ
        # ЕГО РАССЫЛКИ, — и получал ту же страницу молча, неотличимо от
        # «ничего не произошло». Код реестра рисуется общей областью шелла,
        # поэтому сохранение наконец отвечает.
        return RedirectResponse(url=f"/profile?notice={notices.PROFILE_SAVED}", status_code=302)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "profile",
            "timezone_choices": TIMEZONE_CHOICES,
            "error": "Неверный часовой пояс",
        },
        status_code=400,
    )

