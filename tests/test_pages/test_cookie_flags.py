"""Признак транспортной защиты cookie сессии — НАСТРОЙКА, а не литерал (CR-03, Ф-9).

ПОЧЕМУ ЭТОТ ФАЙЛ ДЕРЖИТ ОБЕ ВЕТКИ, А НЕ ОДНУ «ПРАВИЛЬНУЮ». Прод-nginx выбирает
шаблон на лету и при отсутствии сертификата слушает ТОЛЬКО незащищённый порт,
редиректа не делая [docker-compose.prod.yml:43-54, nginx/nginx-http.conf.template].
Признак `secure`, выставленный литералом, в этот момент отменяет вход в продукт
целиком: браузер просто не сохранит cookie, а человеку это видно как «пароль не
подходит». Поэтому тест с ВЫКЛЮЧЕННОЙ настройкой здесь не «негативный случай» —
это утверждение о том, что аварийный выключатель существует и работает.

ПОЧЕМУ СРАВНИВАЮТСЯ НАБОРЫ АТРИБУТОВ, А НЕ ОТДЕЛЬНЫЕ ЗНАЧЕНИЯ (Pitfall 9).
Браузер сопоставляет cookie по имени, пути и домену, а `secure` определяет,
уйдёт ли она вообще. Установка, получившая один набор, и снятие, объявившее
свой набор по умолчанию, расходятся молча: cookie переживает выход, и увидеть
это можно только сравнив НАБОРЫ. Тот же довод делает предметом проверки
равенство наборов у двух точек установки — входа и завершения регистрации:
именно на это равенство встаёт перевыпуск токена при возврате из имперсонации
(план 06-12).
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.services.auth_service import create_verification_token

# Атрибуты, по которым браузер СОПОСТАВЛЯЕТ cookie установки и снятия. Перечень
# выписан ЗДЕСЬ, а не выведен из ответа: тест, берущий ожидание из проверяемого,
# согласился бы с любой правкой. `expires`/`max-age` в него не входят намеренно —
# снятие обязано их добавлять, и требовать их совпадения значило бы запретить
# снятие как таковое.
IDENTITY_ATTRS = ("path", "domain", "samesite", "secure", "httponly")

COOKIE_NAME = "access_token"


def _cookie_attrs(response, name: str = COOKIE_NAME) -> dict[str, object]:
    """Разбор заголовка `Set-Cookie` названной cookie в словарь атрибутов.

    Читается СЫРОЙ заголовок, а не банка клиента: банка хранит значение и
    забывает, с какими атрибутами оно приехало, — а предмет проверки здесь ровно
    атрибуты. Флаги без значения (`Secure`, `HttpOnly`) кладутся как `True`.
    """
    for raw in response.headers.get_list("set-cookie"):
        parts = [p.strip() for p in raw.split(";")]
        key, _, _value = parts[0].partition("=")
        if key != name:
            continue
        attrs: dict[str, object] = {}
        for part in parts[1:]:
            attr_key, sep, attr_value = part.partition("=")
            attrs[attr_key.strip().lower()] = attr_value.strip() if sep else True
        return attrs
    raise AssertionError(
        f"в ответе нет заголовка Set-Cookie для {name!r}: "
        f"{response.headers.get_list('set-cookie')!r}"
    )


def _identity(attrs: dict[str, object]) -> dict[str, object]:
    """Подмножество атрибутов, по которым браузер сопоставляет cookie."""
    return {key: attrs[key] for key in IDENTITY_ATTRS if key in attrs}


def _client_with(settings: Settings, db_session) -> AsyncClient:
    """Клиент приложения, собранного с ПЕРЕДАННЫМИ настройками.

    Фикстура `client` из conftest жёстко берёт `test_settings`, а предмет этого
    файла — поведение при ДВУХ разных значениях одной настройки; собственная
    сборка приложения здесь дешевле, чем параметризация общей фикстуры,
    которую читает вся суита.
    """
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: settings
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest_asyncio.fixture
async def secure_settings(test_settings: Settings) -> Settings:
    """Настройки с ВКЛЮЧЁННЫМ признаком транспортной защиты cookie."""
    return test_settings.model_copy(update={"cookie_secure": True})


@pytest_asyncio.fixture
async def plain_settings(test_settings: Settings) -> Settings:
    """Настройки с ВЫКЛЮЧЕННЫМ признаком — режим HTTP-only nginx."""
    return test_settings.model_copy(update={"cookie_secure": False})


async def _register(db_session, email: str = "cookie@test.com", password: str = "testpass123"):
    """Пользователь в базе — напрямую через ORM, чтобы вход не зависел от регистрации."""
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(email=email, password_hash=hash_password(password), name="Cookie User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_secure_flag_present_when_setting_enabled(secure_settings, db_session):
    """Тест 1: при включённой настройке cookie входа несёт признак транспортной защиты."""
    await _register(db_session)
    async with _client_with(secure_settings, db_session) as client:
        response = await client.post(
            "/login",
            data={"email": "cookie@test.com", "password": "testpass123"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert _cookie_attrs(response).get("secure") is True


@pytest.mark.asyncio
async def test_login_works_and_cookie_kept_when_setting_disabled(plain_settings, db_session):
    """Тест 2: при ВЫКЛЮЧЕННОЙ настройке вход по незащищённому протоколу живой.

    Признака нет, отказа нет, и защищённая страница открывается — то есть
    аварийный выключатель Ф-9 действительно выключает, а не ломает.
    """
    await _register(db_session)
    async with _client_with(plain_settings, db_session) as client:
        response = await client.post(
            "/login",
            data={"email": "cookie@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
        assert "secure" not in _cookie_attrs(response)
        assert client.cookies.get(COOKIE_NAME)

        dashboard = await client.get("/dashboard", follow_redirects=False)
        assert dashboard.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("cookie_secure", [False, True])
async def test_httponly_and_samesite_do_not_depend_on_setting(
    test_settings, db_session, cookie_secure
):
    """Тест 3: запрет доступа из скрипта и политика межсайтовой отправки — в ОБОИХ режимах."""
    settings = test_settings.model_copy(update={"cookie_secure": cookie_secure})
    await _register(db_session)
    async with _client_with(settings, db_session) as client:
        response = await client.post(
            "/login",
            data={"email": "cookie@test.com", "password": "testpass123"},
            follow_redirects=False,
        )

    attrs = _cookie_attrs(response)
    assert attrs.get("httponly") is True
    assert str(attrs.get("samesite", "")).lower() == "lax"


@pytest.mark.asyncio
async def test_both_set_points_emit_the_same_attribute_set(secure_settings, db_session):
    """Тест 4: вторая точка установки (завершение регистрации) даёт ТОТ ЖЕ набор.

    Сравниваются НАБОРЫ, а не отдельные значения: на равенство наборов встаёт
    перевыпуск токена при возврате из имперсонации (план 06-12, Pitfall 9).
    """
    await _register(db_session)
    async with _client_with(secure_settings, db_session) as client:
        login = await client.post(
            "/login",
            data={"email": "cookie@test.com", "password": "testpass123"},
            follow_redirects=False,
        )

        token = create_verification_token(
            "fresh@test.com", secure_settings.secret_key, verified=True
        )
        complete = await client.post(
            "/register/complete",
            data={"token": token, "name": "Fresh User", "password": "testpass123"},
            follow_redirects=False,
        )

    assert complete.status_code == 302
    login_attrs = _cookie_attrs(login)
    complete_attrs = _cookie_attrs(complete)
    assert login_attrs == complete_attrs, (
        "две точки установки cookie объявили РАЗНЫЕ наборы атрибутов: "
        f"вход {login_attrs!r}, завершение регистрации {complete_attrs!r}"
    )
    # Сеансовая форма cookie не должна измениться молча: срока жизни у неё нет.
    assert "max-age" not in login_attrs and "expires" not in login_attrs


@pytest.mark.asyncio
@pytest.mark.parametrize("cookie_secure", [False, True])
async def test_clear_uses_the_same_attribute_set_as_set(test_settings, db_session, cookie_secure):
    """Тест 5: снятие при выходе — тот же набор сопоставляющих атрибутов, и выход работает."""
    settings = test_settings.model_copy(update={"cookie_secure": cookie_secure})
    await _register(db_session)
    async with _client_with(settings, db_session) as client:
        login = await client.post(
            "/login",
            data={"email": "cookie@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        logout = await client.get("/logout", follow_redirects=False)

        assert logout.status_code == 302
        assert _identity(_cookie_attrs(logout)) == _identity(_cookie_attrs(login)), (
            "снятие cookie объявило не тот набор атрибутов, что установка — "
            "браузер может не сопоставить их, и cookie переживёт выход"
        )

        after = await client.get("/dashboard", follow_redirects=False)
        assert after.status_code == 302
        assert after.headers["location"] == "/login"


def test_setting_default_is_disabled():
    """Тест 6: умолчание настройки в модели — ВЫКЛЮЧЕНО.

    Включённое умолчание отняло бы вход у локальной разработки и у суиты, а на
    бою — у всех сразу в тот момент, когда сертификат не продлился (Ф-9).
    Безопасное значение живёт в боевом артефакте, где его выключают одной
    переменной, не выкатывая код.
    """
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
    )
    assert settings.cookie_secure is False
