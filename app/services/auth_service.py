from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ИМЯ ПРИЗНАКА ДЕЙСТВУЮЩЕГО ЛИЦА — КОНСТАНТОЙ, А НЕ ЛИТЕРАЛОМ В ЧЕТЫРЁХ МЕСТАХ.
# Выпуск, чтение и единственный читатель ниже обязаны набирать одно и то же
# слово; разошедшийся литерал выглядел бы как «признака нет» — то есть как
# штатное отсутствие имперсонации, а не как опечатка.
ACTOR_CLAIM = "act"

# СРОК ЖИЗНИ ОБЫЧНОГО ТОКЕНА — тот же, что был выписан умолчанием в сигнатуре.
# Константа заведена ради сравнения со сроком имперсонации: пока обычный срок
# жил литералом, «короче обычного» нельзя было утверждать иначе как второй
# копией числа в тесте.
ACCESS_EXPIRE_MINUTES = 1440

# СРОК ЖИЗНИ ТОКЕНА ИМПЕРСОНАЦИИ — ОТДЕЛЬНЫЙ И КОРОТКИЙ (D-25).
#
# ПРИЧИНА, А НЕ ЧИСЛО. Обычный токен живёт сутки, и это верно для человека,
# работающего в СВОЕЙ учётной записи. Имперсонация на сутки — это забытая
# открытой ЧУЖАЯ учётная запись: администратор закрыл вкладку, ушёл, а его
# следующее действие в продукте уйдёт от имени другого человека — в том числе
# рассылка в чужие группы, необратимо и без ведома владельца.
#
# Значение названо решением владельца (D-25); внешнего стандарта, предписывающего
# срок для входа администратора под пользователем, исследование не нашло. Оно
# живёт ОДНОЙ константой, и смена — правка одной строки.
IMPERSONATION_EXPIRE_MINUTES = 60


def create_access_token(
    user_id: int,
    secret_key: str,
    expires_minutes: int = ACCESS_EXPIRE_MINUTES,
    *,
    actor_id: int | None = None,
) -> str:
    """Единственная точка выпуска токена доступа на проект.

    ⚠️ ПАРАМЕТР ДЕЙСТВУЮЩЕГО ЛИЦА — ИМЕНОВАННЫЙ-ТОЛЬКО, И ЭТО НЕСУЩЕЕ СВОЙСТВО,
    А НЕ СТИЛЬ. Все существующие вызовы позиционные, и третьим позиционным
    аргументом у них едет СРОК; позиционный параметр действующего лица встал бы
    следом и молча принял бы значение, которого ему никто не давал. Закреплено
    `test_the_actor_parameter_is_keyword_only_so_positional_calls_are_untouched`.

    ⚠️ ПРИЗНАК ДОПИСЫВАЕТСЯ ТОЛЬКО КОГДА ДЕЙСТВУЮЩЕЕ ЛИЦО УКАЗАНО (D-21).
    Отсутствие указания обязано давать прежнюю нагрузку байт-в-байт: лишнее
    поле здесь меняет ВСЕ токены проекта разом — вход, все JSON-маршруты и все
    страницы. Закреплено сравнением МНОЖЕСТВА ключей, а не глазами.

    ⚠️ ФОРМА ЗНАЧЕНИЯ — ОБЪЕКТ С ВЛОЖЕННЫМ ИДЕНТИФИКАТОРОМ, А НЕ СКАЛЯР, и
    выбор записан явно. Это форма внешнего стандарта делегирования (RFC 8693,
    claim `act`), и вложенность внутри него записывает ЦЕПОЧКУ делегирования —
    то есть оставляет место третьему лицу (поддержка, вошедшая под
    администратором). Скаляр работал бы и был бы проще, но перестал бы быть
    формой стандарта, а значит следующий читатель токена — например, внешний
    инструмент — прочитал бы его неверно.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    if actor_id is not None:
        payload[ACTOR_CLAIM] = {"sub": str(actor_id)}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict | None:
    """Единственная точка чтения токена доступа на проект.

    ⚠️ ПРИВЕДЕНИЕ ТИПА ИДЕНТИФИКАТОРА ДЕЙСТВУЮЩЕГО ЛИЦА ЖИВЁТ ЗДЕСЬ, РЯДОМ С
    ПРИВЕДЕНИЕМ СУБЪЕКТА, И ЭТО ПРЕДМЕТ. Читателей у разобранной нагрузки
    несколько (аутентификатор, соседняя зависимость блокировки, страничный
    путь), и приведи его каждый сам — один сравнил бы строку, другой число.
    Расхождение проявилось бы не исключением, а «админ-доступ пропал» ровно у
    одного из потребителей.

    ⚠️ ИСПОРЧЕННЫЙ ПРИЗНАК ЕСТЬ ЕГО ОТСУТСТВИЕ, А НЕ ОТКАЗ ЧТЕНИЯ. Чтение и так
    устроено так, что неразбираемое даёт отказ целиком; сделай признак новым
    способом уронить чтение — и запрос с подпорченным полем превратился бы из
    «вошёл как обычно» в «не вошёл вовсе». Ключ в этом случае СНИМАЕТСЯ, а не
    обнуляется: единственный читатель ниже спрашивает про отсутствие, и
    оставленный ключ с пустым значением ответил бы ему «действующее лицо есть».

    ⚠️ СКАЛЯРНАЯ ФОРМА ПРИЗНАКА ПРИНИМАЕТСЯ НА ЧТЕНИЕ, ХОТЯ НЕ ВЫПУСКАЕТСЯ.
    Выпуск всегда пишет объектную форму стандарта; чтение терпимо к скаляру,
    потому что такие токены в проекте уже есть — план 06-06 собрал их вручную,
    закрепляя ветку D-26 до того, как появился выпуск. Терпимость односторонняя
    и названа здесь, чтобы её не приняли за вторую поддерживаемую форму.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        payload["sub"] = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None

    if ACTOR_CLAIM in payload:
        claim = payload[ACTOR_CLAIM]
        raw = claim.get("sub") if isinstance(claim, dict) else claim
        # Логическое значение — не идентификатор, хотя `int()` его принимает:
        # `True` доехал бы до читателя единицей, то есть НАСТОЯЩИМ чужим
        # пользователем, а не отказом.
        if isinstance(raw, bool):
            raw = None
        try:
            payload[ACTOR_CLAIM] = {"sub": int(raw)}
        except (TypeError, ValueError):
            payload.pop(ACTOR_CLAIM)

    return payload


def actor_id(payload: dict | None) -> int | None:
    """Идентификатор ДЕЙСТВУЮЩЕГО ЛИЦА из уже разобранной нагрузки, либо `None`.

    ЕДИНСТВЕННЫЙ ЧИТАТЕЛЬ ПРИЗНАКА НА ПРОЕКТ. Форма значения — объектная, и
    навигация по ней («взять вложенное поле») не имеет права расползтись по
    потребителям: смена формы под цепочку из трёх лиц тогда потребовала бы
    ревизии каждого места чтения токена вместо правки одной функции.

    Приведения типа здесь НЕТ намеренно — оно уже сделано чтением токена. Второе
    приведение на этом месте означало бы, что читатель не доверяет чтению, и
    первый же потребитель, скопировавший его себе, завёл бы третье.
    """
    if not payload:
        return None
    claim = payload.get(ACTOR_CLAIM)
    if not isinstance(claim, dict):
        return None
    return claim.get("sub")


def create_verification_token(
    email: str, secret_key: str, verified: bool = False,
    expires_minutes: int = 30, purpose: str = "email_verification"
) -> str:
    """Create a JWT token for email verification or password reset flow."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"email": email, "verified": verified, "exp": expire, "purpose": purpose}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_verification_token(token: str, secret_key: str) -> dict | None:
    """Decode a verification JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if payload.get("purpose") not in ("email_verification", "password_reset"):
            return None
        return payload
    except (JWTError, KeyError, ValueError):
        return None
