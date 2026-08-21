"""Пробный срок заводится ОБОИМИ путями регистрации и ОДНОЙ функцией (D-B).

ПРЕДМЕТ ФАЙЛА. Входов регистрации в продукте два: страничный
`POST /register/complete` (три шага с подтверждением адреса) и JSON
`POST /api/auth/register`. Пробный срок обязан появляться на ОБОИХ и быть
ОДИНАКОВОЙ длины — иначе человек, зарегистрировавшийся «не тем» способом,
получил бы другой продукт, и заметил бы это не он, а поддержка.

ПОЧЕМУ ДЛИНА ЧИТАЕТСЯ ИЗ `app.constants`, А НЕ ВЫПИСАНА ЧИСЛОМ. Тест, знающий
длину пробного периода собственным литералом, перестаёт ловить её изменение: он
и код разойдутся молча, и зелёный тест будет означать «два числа совпали
когда-то». Импорт делает тест свидетелем константы, а не её копией.
"""
from datetime import datetime, timedelta, timezone
import re

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import TRIAL_DAYS
from app.models.email_verification import EmailVerificationCode
from app.models.subscription import Subscription
from app.models.user import User

# Допуск сверки срока. Между вызовом маршрута и чтением строки проходит
# ненулевое время, поэтому равенство «до микросекунды» было бы утверждением о
# скорости машины, а не о длине пробного периода.
TOLERANCE = timedelta(minutes=1)


async def _rows_of(db: AsyncSession, email: str) -> list[Subscription]:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one()
    return list(
        (
            await db.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )


def _aware(value: datetime) -> datetime:
    """SQLite отдаёт `DateTime(timezone=True)` NAIVE, PostgreSQL — aware."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _assert_trial(rows: list[Subscription], started_at: datetime, path: str) -> None:
    """Ровно одна активная строка с концом срока в `started_at + TRIAL_DAYS`."""
    assert len(rows) == 1, (
        f"{path}: строк подписки {len(rows)}, а обещана ровно одна — "
        "вторая означала бы второе заведение пробного срока"
    )
    row = rows[0]
    assert row.is_active is True, f"{path}: пробная строка заведена неактивной"

    expected = started_at + timedelta(days=TRIAL_DAYS)
    actual = _aware(row.expires_at)
    assert expected - TOLERANCE <= actual <= expected + TOLERANCE, (
        f"{path}: конец пробного срока {actual}, ожидался около {expected} "
        f"(TRIAL_DAYS = {TRIAL_DAYS})"
    )


@pytest.mark.asyncio
async def test_the_page_registration_path_starts_the_trial(
    client: AsyncClient, db_session: AsyncSession
):
    """Страничный `POST /register/complete` заводит пробный срок."""
    email = "trial-pages@test.com"
    started_at = datetime.now(timezone.utc)

    response = await client.post("/register/send-code", data={"email": email})
    token = re.search(r'name="token" value="([^"]+)"', response.text).group(1)

    code_record = (
        await db_session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == email
            )
        )
    ).scalar_one()

    response = await client.post(
        "/register/verify", data={"token": token, "code": code_record.code}
    )
    verified_token = re.search(r'name="token" value="([^"]+)"', response.text).group(1)

    response = await client.post(
        "/register/complete",
        data={"token": verified_token, "name": "Trial Pages", "password": "securepass123"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    _assert_trial(
        await _rows_of(db_session, email), started_at, "POST /register/complete"
    )


@pytest.mark.asyncio
async def test_the_json_registration_path_starts_the_trial(
    client: AsyncClient, db_session: AsyncSession
):
    """JSON `POST /api/auth/register` заводит ТОТ ЖЕ пробный срок.

    Второй путь регистрации существует и обслуживает в том числе фикстуры всей
    суиты (`auth_headers` в `tests/conftest.py`). Пока он не заводил пробной
    строки, каждый зарегистрированный им пользователь встречал продукт с
    закрытым доступом.
    """
    email = "trial-json@test.com"
    started_at = datetime.now(timezone.utc)

    response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "securepass123", "name": "Trial Json"},
    )
    assert response.status_code == 201

    _assert_trial(
        await _rows_of(db_session, email), started_at, "POST /api/auth/register"
    )


@pytest.mark.asyncio
async def test_the_two_paths_agree_on_the_length_of_the_trial(
    client: AsyncClient, db_session: AsyncSession
):
    """Оба входа дают ОДИН и тот же срок — иначе функция заведения не одна.

    Утверждение отдельное от двух предыдущих намеренно: каждое из них сверяет
    свой путь с константой ПО ОТДЕЛЬНОСТИ, и оба остались бы зелёными, если бы
    длину задавали две копии одного числа, случайно совпавшие. Здесь сверяются
    ДВА ПОЛУЧЕННЫХ СРОКА между собой — расхождение копий стало бы видно даже
    при верной константе.
    """
    page_email = "agree-pages@test.com"
    json_email = "agree-json@test.com"

    response = await client.post("/register/send-code", data={"email": page_email})
    token = re.search(r'name="token" value="([^"]+)"', response.text).group(1)
    code_record = (
        await db_session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == page_email
            )
        )
    ).scalar_one()
    response = await client.post(
        "/register/verify", data={"token": token, "code": code_record.code}
    )
    verified_token = re.search(r'name="token" value="([^"]+)"', response.text).group(1)
    await client.post(
        "/register/complete",
        data={"token": verified_token, "name": "A", "password": "securepass123"},
        follow_redirects=False,
    )

    await client.post(
        "/api/auth/register",
        json={"email": json_email, "password": "securepass123", "name": "B"},
    )

    page_expiry = _aware((await _rows_of(db_session, page_email))[0].expires_at)
    json_expiry = _aware((await _rows_of(db_session, json_email))[0].expires_at)

    assert abs(page_expiry - json_expiry) <= TOLERANCE, (
        f"пути регистрации дали разные сроки: {page_expiry} и {json_expiry} — "
        "заведение пробной строки объявлено дважды"
    )
