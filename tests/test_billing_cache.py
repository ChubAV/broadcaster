"""Кэшированный вердикт ДОСТУПА: форма файла прежняя, предмет — новый.

ЧЕТЫРЕ ТЕСТА ТОЙ ЖЕ СТРУКТУРЫ, ЧТО У КЭША БАЛАНСА, И ЭТО НЕ ЛЕНЬ. Кэшированный
гейт доступа обязан повторять форму предшественника ДОСЛОВНО — сигнатуру
`(db, user_id, action) -> tuple[bool, str]`, ранний выход по `action != "send"`,
чтение и запись через `_get_redis`, деградацию без Redis, — потому что ровно эта
форма есть контракт параметра `check_limit` у `collect_due_schedules`
(`app/application/scheduling/use_cases.py:129-134`). Разойдись она хоть одним
элементом, подстановка нового гейта в путь отправки перестала бы быть заменой
имени и стала бы правкой поведения.

⚠️ КЛЮЧ КЭША ПРОВЕРЯЕТСЯ ЯВНО, А НЕ ПОДРАЗУМЕВАЕТСЯ. Значение под ключом
поменяло СМЫСЛ: раньше там лежал ответ «есть ли сообщения на балансе», теперь —
«открыт ли доступ». Сохранить имя `balance:{user_id}` значило бы получить после
выката минуту, в которой закэшированные ответы о балансе читаются как ответы о
доступе, — то есть неверные вердикты авторизации, ничем не отличимые от верных.
Поэтому `test_check_access_cached_uses_cache` утверждает ИМЯ ключа, а не только
факт попадания.

СТАРАЯ ПАРА ФУНКЦИЙ ОСТАТКА СНЯТА ВМЕСТЕ С САМИМ СПИСАНИЕМ СООБЩЕНИЙ, И ПОРЯДОК
БЫЛ НЕСУЩИМ: гейт доступа введён РАНЬШЕ, и между двумя коммитами путь отправки
был закрыт хотя бы одним из двух. Снятие первым оставило бы окно, в котором
рассылка идёт без гейта вовсе.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.billing_cache import check_access_cached


def _mock_settings():
    s = MagicMock()
    s.redis_url = "redis://localhost:6379/0"
    s.billing_cache_ttl = 60
    return s


@pytest.mark.asyncio
async def test_check_access_cached_returns_result():
    """Без Redis вердикт считается в базе и отдаётся кортежем `(bool, str)`."""
    mock_db = AsyncMock()
    with patch(
        "app.services.billing_cache.check_access", return_value=(True, "")
    ) as mock_check:
        with patch("app.services.billing_cache._get_redis", return_value=None):
            with patch(
                "app.services.billing_cache.get_settings",
                return_value=_mock_settings(),
            ):
                result = await check_access_cached(mock_db, user_id=1, action="send")
    assert result == (True, "")
    mock_check.assert_called_once_with(mock_db, 1)


@pytest.mark.asyncio
async def test_check_access_cached_non_send_always_allows():
    """Ранний выход по действию: всё, кроме отправки, разрешено без БД и без Redis.

    Утверждение о НЕОБРАЩЕНИИ к базе здесь несущее, а не декоративное: гейт
    зовётся в цикле планировщика по каждому расписанию, и потеря раннего выхода
    превратила бы его в запрос на строку.
    """
    mock_db = AsyncMock()
    result = await check_access_cached(mock_db, user_id=1, action="create_ad")
    assert result == (True, "")
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_check_access_cached_uses_cache():
    """Готовый вердикт читается из Redis по ключу `access:{user_id}` — без БД."""
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value='{"allowed": true, "reason": ""}')

    with patch("app.services.billing_cache._get_redis", return_value=mock_redis):
        with patch(
            "app.services.billing_cache.get_settings", return_value=_mock_settings()
        ):
            with patch("app.services.billing_cache.check_access") as mock_check:
                result = await check_access_cached(mock_db, user_id=1, action="send")
    assert result == (True, "")
    mock_check.assert_not_called()
    mock_redis.get.assert_awaited_once_with("access:1"), (
        "вердикт доступа читается не из своего ключа — имя пережило смену смысла"
    )


@pytest.mark.asyncio
async def test_check_access_cached_falls_back_on_redis_error():
    """Недоступный Redis не отменяет вердикт: он считается прямо в базе."""
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=Exception("Redis down"))

    with patch("app.services.billing_cache._get_redis", return_value=mock_redis):
        with patch(
            "app.services.billing_cache.get_settings", return_value=_mock_settings()
        ):
            with patch(
                "app.services.billing_cache.check_access",
                return_value=(False, "access_closed"),
            ) as mock_check:
                result = await check_access_cached(mock_db, user_id=1, action="send")
    assert result == (False, "access_closed")
    mock_check.assert_called_once()
