"""Источник кодов подтверждения — криптографический, и утверждается ИСТОЧНИК (CR-02).

⚠️ ПОЧЕМУ ЭТОТ ФАЙЛ ЧИТАЕТ ИСХОДНИК, А НЕ СРАВНИВАЕТ ЗНАЧЕНИЯ. Вывод
псевдослучайного генератора общего назначения и вывод криптографического — это
в обоих случаях шесть десятичных цифр. Никакой тест, смотрящий на РЕЗУЛЬТАТ, не
отличит починенный код от непочиненного: распределения совпадают, длины
совпадают, типы совпадают. Тест, написанный «по значению», был бы зелёным и до
правки — то есть сертифицировал бы несделанную работу. Предмет проверки здесь
ровно один: КАКОЙ МОДУЛЬ позван.

⚠️ И ПОЧЕМУ ПО ДЕРЕВУ, А НЕ ГРЕПОМ. Греп по строке `random` считает её и в
комментарии, и в докстринге, и в слове `randbelow`; вопрос же здесь — какие
имена импортированы и какие функции вызваны. Форма разбора заимствована у
машинного гейта роутеров (`tests/test_pages/test_access_gate.py`), который по
тому же доводу читает вызовы `include_router` деревом, а не поиском строки.

TTL кода и лимит попыток защитой от предсказания НЕ являются: они ограничивают
ПЕРЕБОР, а предсказание перебором не является — поэтому смены источника ничем
другим в продукте не заменить.
"""
import ast
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.email_verification import EmailVerificationCode
from app.models.user import User
from app.pages.auth import CODE_LENGTH
from app.services.auth_service import hash_password

AUTH_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "auth.py"

# Имя псевдослучайного генератора общего назначения, которого в модуле быть не
# должно. Строка собирается, а не пишется целиком, чтобы этот файл не краснил
# сам себя грепом дисциплины по запрещённому имени.
WEAK_SOURCE = "rand" + "om"

# Имя криптографического модуля стандартной библиотеки, который его заменил.
STRONG_SOURCE = "secrets"

# СКОЛЬКО МЕСТ ГЕНЕРАЦИИ КОДА В МОДУЛЕ. Число выписано ЗДЕСЬ, а не выведено из
# исходника: тест, берущий ожидание из проверяемого, согласился бы с любой
# правкой — в том числе с пятым местом, заведённым будущим планом и оставленным
# на старом источнике. Изменение этого числа обязано быть решением, записанным
# в двух местах сразу.
EXPECTED_GENERATION_SITES = 4


def _tree() -> ast.Module:
    return ast.parse(AUTH_PY.read_text(encoding="utf-8"))


def _imported_module_names(tree: ast.Module) -> set[str]:
    """Все имена модулей, импортированных в разбираемом файле.

    Учитываются обе формы — `import X` и `from X import ...`, — потому что
    вернуть старый источник можно любой из них, и утверждение, знающее только
    первую, закрывало бы половину двери.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def _calls_on_module(tree: ast.Module, module: str) -> list[str]:
    """Имена функций, позванных как `<module>.<func>(...)`."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if isinstance(func.value, ast.Name) and func.value.id == module:
            found.append(func.attr)
    return found


def test_weak_random_is_not_imported():
    """Тест 1: псевдослучайного генератора общего назначения нет среди импортов.

    Импорт снят целиком, а не оставлен «на всякий случай»: другого применения у
    него в модуле нет, и оставленное имя было бы приглашением вернуть старый
    вызов следующей правкой.
    """
    assert WEAK_SOURCE not in _imported_module_names(_tree())


def test_crypto_source_is_imported():
    """Тест 2: криптографический модуль стандартной библиотеки импортирован."""
    assert STRONG_SOURCE in _imported_module_names(_tree())


def test_no_call_of_the_weak_source_remains():
    """Тест 3: в модуле нет ни одного вызова старого генератора.

    Обход ВСЕХ узлов вызова, а не поиск строки: строка `random` встречается и
    внутри имени функции нового источника, и в объяснениях.
    """
    assert _calls_on_module(_tree(), WEAK_SOURCE) == []


def test_all_generation_sites_use_the_crypto_source():
    """Тест 4: мест генерации ровно столько, сколько объявлено, и все — на новом источнике.

    Пятое место, заведённое будущим планом на старом источнике, обязано
    покраснить этот тест, а не промолчать.
    """
    calls = _calls_on_module(_tree(), STRONG_SOURCE)
    assert len(calls) == EXPECTED_GENERATION_SITES, (
        f"мест обращения к {STRONG_SOURCE} в модуле {len(calls)}, "
        f"а объявлено {EXPECTED_GENERATION_SITES}: {calls}"
    )


@pytest.mark.asyncio
async def test_generated_code_keeps_its_shape(client, db_session):
    """Тест 5: форма значения не изменилась — те же десятичные цифры, та же длина.

    Утверждение НЕ об источнике: оно закрывает ровно ту половину, где смена
    источника могла бы молча поменять алфавит или длину кода и сломать приём.
    """
    response = await client.post(
        "/register/send-code", data={"email": "shape@test.com"}
    )
    assert response.status_code == 200

    record = (
        await db_session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == "shape@test.com"
            )
        )
    ).scalar_one()

    assert len(record.code) == CODE_LENGTH
    assert record.code.isdigit()


@pytest.mark.asyncio
async def test_issued_code_is_still_accepted_end_to_end(client, db_session):
    """Тест 6: сквозной сценарий подтверждения принимает выданный код.

    Берётся путь ВОССТАНОВЛЕНИЯ ДОСТУПА — тот самый, ради которого
    предсказуемость кода была критической: захват учётки шёл через него.
    """
    db_session.add(
        User(
            email="e2e@test.com",
            password_hash=hash_password("oldpassword"),
            name="E2E User",
        )
    )
    await db_session.commit()

    sent = await client.post(
        "/forgot-password/send-code", data={"email": "e2e@test.com"}
    )
    assert sent.status_code == 200

    record = (
        await db_session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == "e2e@test.com",
                EmailVerificationCode.purpose == "password_reset",
            )
        )
    ).scalar_one()

    token = _token_from(sent.text)
    verified = await client.post(
        "/forgot-password/verify", data={"token": token, "code": record.code}
    )
    assert verified.status_code == 200
    assert "Неверный код" not in verified.text
    assert 'name="password"' in verified.text


def _token_from(html: str) -> str:
    """Значение скрытого поля `token` со страницы подтверждения."""
    import re

    match = re.search(r'name="token"\s+value="([^"]+)"', html)
    if match is None:
        match = re.search(r'value="([^"]+)"\s+name="token"', html)
    assert match is not None, "на странице подтверждения нет скрытого поля token"
    return match.group(1)
