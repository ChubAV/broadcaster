"""Признак ДЕЙСТВУЮЩЕГО ЛИЦА в единственной точке выпуска и чтения токена.

ЗАЧЕМ ОТДЕЛЬНЫЙ ФАЙЛ. `tests/test_services/test_auth_service.py` держит предмет
«пароли и токены подтверждения» и знает о токене доступа ровно одно: субъект
доезжает целым числом. Здесь предмет другой и он новый — в ОДНОМ токене едут
ДВЕ личности: субъект (чью учётную запись открыли) и действующее лицо (кто
действует). Разложить это по соседнему файлу значило бы спрятать самое
чувствительное утверждение фазы среди проверок хеширования пароля.

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА — ПЕРВОЕ, А НЕ ПОСЛЕДНЕЕ (D-21). Токен БЕЗ
действующего лица обязан давать прежний состав полезной нагрузки, и это
проверяется сравнением МНОЖЕСТВА КЛЮЧЕЙ, а не аккуратностью правки: лишнее поле
в нагрузке меняет ВСЕ токены проекта разом — вход, все JSON-маршруты и все
страницы, — и заметить это глазами при ревью нельзя.

⚠️ ТИП ИДЕНТИФИКАТОРА ДЕЙСТВУЮЩЕГО ЛИЦА ЗАКРЕПЛЁН ЗДЕСЬ, А НЕ У ЧИТАТЕЛЕЙ.
Приведение живёт ВНУТРИ чтения токена рядом с приведением субъекта: иначе один
читатель сравнил бы строку, другой — число, и расхождение проявилось бы как
«админ-доступ пропал» ровно у одного из потребителей.
"""
from datetime import datetime, timedelta, timezone
import inspect

import pytest
from jose import jwt

from app.services import auth_service as auth

SECRET = "test-secret-key"


def _payload(token: str) -> dict:
    """Сырая нагрузка токена — БЕЗ приведения типов чтением проекта.

    Утверждение о СОСТАВЕ нагрузки нельзя снимать функцией, которая эту
    нагрузку и правит: она добавляет и убирает ключи, и тест мерил бы её
    поведение вместо содержимого токена.
    """
    return jwt.decode(token, SECRET, algorithms=["HS256"])


# --- Тест 1 (D-21): прежний токен не изменился ни одним ключом ---------------

def test_a_token_without_act_keeps_the_previous_payload_key_set():
    """Нагрузка токена без действующего лица — РОВНО прежнее множество ключей.

    Сравнивается множество, а не отдельные значения: предмет утверждения —
    ОТСУТСТВИЕ лишнего поля, а отсутствие проверяется только сравнением
    целиком. Проверка вида «sub на месте» зеленела бы при любом числе
    дописанных полей.
    """
    token = auth.create_access_token(user_id=42, secret_key=SECRET)

    assert set(_payload(token)) == {"sub", "exp"}, (
        "состав полезной нагрузки обычного токена изменился — правка достала "
        "ВСЕ токены проекта разом (D-21)"
    )


# --- Тест 2: токен с действующим лицом ---------------------------------------

def test_a_token_with_an_actor_adds_the_claim_and_keeps_the_subject_form():
    """Признак ДОПИСЫВАЕТСЯ, а форма субъекта остаётся прежней.

    Форма значения признака — ОБЪЕКТ с вложенным идентификатором, а не скаляр:
    это форма внешнего стандарта делегирования (RFC 8693), и она оставляет
    место цепочке более чем из двух лиц. Скаляр работал бы и был бы проще, но
    перестал бы быть формой стандарта — то есть следующий читатель токена
    прочитал бы его неверно.
    """
    token = auth.create_access_token(user_id=42, secret_key=SECRET, actor_id=7)
    payload = _payload(token)

    assert set(payload) == {"sub", "exp", "act"}, (
        "признак действующего лица не доехал до нагрузки или привёл с собой "
        "лишние поля"
    )
    assert payload["sub"] == "42", "форма субъекта в нагрузке изменилась"
    assert payload["act"] == {"sub": "7"}, (
        "значение признака не объектной формы стандарта делегирования"
    )


# --- Тест 3: приведение типа живёт внутри чтения -----------------------------

def test_the_actor_id_is_coerced_where_the_subject_id_is_coerced():
    """Оба идентификатора приведены к ОДНОМУ типу в ОДНОМ месте.

    Сравнение с целым числом истинно — значит, ни один читатель не обязан
    приводить признак сам. Читатель, приводящий его у себя, — это второе
    объявление правила, и разойтись им есть на чём.
    """
    token = auth.create_access_token(user_id=42, secret_key=SECRET, actor_id=7)
    payload = auth.decode_access_token(token, SECRET)

    assert payload is not None
    assert payload["sub"] == 42
    assert auth.actor_id(payload) == 7, (
        "идентификатор действующего лица прочитан не тем типом, что субъект"
    )
    assert isinstance(auth.actor_id(payload), int)


# --- Тест 4: отсутствие признака есть ОТСУТСТВИЕ -----------------------------

def test_reading_a_token_without_act_yields_absence_not_an_empty_value():
    """Нет признака — `None`, а не пустая строка и не ноль.

    Ноль и пустая строка ложны наравне с отсутствием ровно до первого
    читателя, который спросит `is not None`, — и там разница становится
    разницей между «действующего лица нет» и «действует пользователь с
    идентификатором 0».
    """
    token = auth.create_access_token(user_id=42, secret_key=SECRET)
    payload = auth.decode_access_token(token, SECRET)

    assert payload is not None
    assert "act" not in payload, "ключ признака появился в токене без имперсонации"
    assert auth.actor_id(payload) is None


# --- Тест 5 (D-25): срок имперсонации — своя короткая константа --------------

def test_the_impersonation_lifetime_is_a_named_constant_and_markedly_shorter():
    """Срок имперсонации объявлен константой и ЗАМЕТНО короче обычного.

    Сравниваются САМИ ЗНАЧЕНИЯ, а не литералы, выписанные в тесте: выписанное
    здесь число было бы второй копией решения владельца и разошлось бы с
    первой молча. «Заметно короче» выражено кратностью, а не разностью, —
    разность зеленела бы при сроке имперсонации в сутки без минуты.
    """
    assert auth.IMPERSONATION_EXPIRE_MINUTES < auth.ACCESS_EXPIRE_MINUTES / 4, (
        "срок имперсонации сопоставим с обычным — забытая открытой чужая "
        "учётная запись живёт столько же, сколько обычный вход (D-25)"
    )

    issued = datetime.now(timezone.utc)
    token = auth.create_access_token(
        user_id=42,
        secret_key=SECRET,
        expires_minutes=auth.IMPERSONATION_EXPIRE_MINUTES,
        actor_id=7,
    )
    expires_at = datetime.fromtimestamp(_payload(token)["exp"], tz=timezone.utc)
    lifetime_minutes = (expires_at - issued).total_seconds() / 60

    assert abs(lifetime_minutes - auth.IMPERSONATION_EXPIRE_MINUTES) < 1, (
        "срок выпущенного токена разошёлся с объявленной константой"
    )


# --- Тест 6: истёкший токен имперсонации отвергается той же веткой -----------

def test_an_expired_impersonation_token_is_refused_like_any_expired_token():
    """Признак действующего лица не переживает истечение срока.

    Ветка та же, что у обычного истёкшего токена: имперсонация не имеет права
    оказаться единственным видом токена, у которого срок ничего не значит.
    """
    expired = jwt.encode(
        {
            "sub": "42",
            "act": {"sub": "7"},
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET,
        algorithm="HS256",
    )

    assert auth.decode_access_token(expired, SECRET) is None


# --- Тест 7: испорченный признак — это его отсутствие, а не отказ чтения -----

@pytest.mark.parametrize(
    "claim",
    [
        pytest.param({}, id="object_without_the_nested_id"),
        pytest.param({"sub": None}, id="nested_id_is_null"),
        pytest.param({"sub": "not-a-number"}, id="nested_id_is_not_numeric"),
        pytest.param({"sub": ["7"]}, id="nested_id_is_a_list"),
        pytest.param([], id="claim_is_a_list"),
        pytest.param(True, id="claim_is_a_boolean"),
    ],
)
def test_a_corrupted_actor_claim_reads_as_absence_and_never_breaks_the_read(claim):
    """Испорченный признак трактуется как отсутствие и НЕ роняет чтение.

    Чтение токена уже устроено так, что неразбираемое даёт отказ целиком.
    Признак не имеет права стать новым способом уронить чтение: тогда любой
    запрос с подпорченным полем превращался бы из «вошёл как обычно» в
    «не вошёл вовсе».
    """
    token = jwt.encode(
        {
            "sub": "42",
            "act": claim,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        SECRET,
        algorithm="HS256",
    )

    payload = auth.decode_access_token(token, SECRET)

    assert payload is not None, "испорченный признак уронил чтение токена целиком"
    assert payload["sub"] == 42, "субъект пострадал от испорченного соседа"
    assert auth.actor_id(payload) is None


# --- Тест 8: существующие вызовы выпуска не сдвинулись ------------------------

def test_the_actor_parameter_is_keyword_only_so_positional_calls_are_untouched():
    """Новый параметр — ИМЕНОВАННЫЙ-ТОЛЬКО, и это несущее свойство.

    Все существующие вызовы выпуска токена позиционные
    (`create_access_token(user.id, secret, expire_minutes)`), и позиционный
    параметр сдвинул бы их МОЛЧА: третьим позиционным аргументом уехал бы срок,
    и вход выдавал бы токены с чужим идентификатором действующего лица.
    """
    parameter = inspect.signature(auth.create_access_token).parameters["actor_id"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
        "параметр действующего лица можно передать позиционно — существующие "
        "вызовы выпуска токена сдвинулись бы молча"
    )
    assert parameter.default is None, (
        "у параметра действующего лица есть умолчание, отличное от его "
        "отсутствия"
    )

    # Прежняя форма вызова — ровно та, что стоит в app/routes/auth.py.
    token = auth.create_access_token(42, SECRET, 30)
    payload = auth.decode_access_token(token, SECRET)

    assert payload is not None and payload["sub"] == 42
    assert auth.actor_id(payload) is None
