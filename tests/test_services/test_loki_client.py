"""Клиент источника логов: НЕДОСТУПНОСТЬ — ОТДЕЛЬНОЕ СОСТОЯНИЕ, А НЕ ПУСТОТА.

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА — `test_an_empty_but_healthy_answer_is_not_unavailable`
в паре с `test_a_refused_connection_is_reported_unavailable_and_does_not_raise`.
Оба возвращают ПУСТОЙ перечень строк, и различить их можно ТОЛЬКО по отдельному
полю результата. Мониторинг в этом проекте опционален и остаётся таким (D-28):
боевые команды запуска и выката его не поднимают, поэтому недоступность
источника — ШТАТНАЯ ветка, а не исключительная. Выведи разметка «источника нет»
из длины списка — и в аварии, ради которой администратор в подраздел и пришёл,
она ответила бы ему «ошибок нет». Это самый дорогой из возможных ответов:
неправдой на единственный заданный вопрос.

⚠️ ПОТОЛОК УЗНАЁТСЯ, А НЕ УГАДЫВАЕТСЯ. Предел выдачи запрашивается на ЕДИНИЦУ
больше потолка показа: лишняя прочитанная строка — единственная улика усечения.
Без неё «прочитано ровно 200» было бы неотличимо от «за окно ровно 200 строк», и
признак пришлось бы выводить из длины — то есть объявлять полный перечень
усечённым. Приём в проекте уже применён дважды (`PAYMENT_LIST_CAP`,
`QUEUE_ROW_CAP`), и граница потолка проверяется здесь ДВУМЯ отдельными случаями.

Ни один тест не требует поднятого источника логов: суита идёт без внешних служб,
и подменяется ИМЕНОВАННАЯ ленивая точка получения клиента —
`app.services.loki_client._client`, ровно тем же приёмом, каким в проекте
подменяются кэш вердикта доступа и сервис оперативного состояния.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.loki_client import (
    LOG_LINE_CAP,
    LOKI_TIMEOUT_SEC,
    query_range,
)


def _ns(moment: datetime) -> str:
    """Момент в наносекундах СТРОКОЙ — ровно так их отдаёт источник."""
    return str(int(moment.timestamp() * 1e9))


def _stream(labels: dict, values: list) -> dict:
    return {"stream": labels, "values": values}


def _payload(*streams) -> dict:
    """Форма ответа источника: {status, data:{resultType, result:[...]}}."""
    return {
        "status": "success",
        "data": {"resultType": "streams", "result": list(streams)},
    }


def _response(payload: dict, *, status: int = 200):
    """Двойник ответа: `raise_for_status` ведёт себя как у настоящего."""
    resp = MagicMock()
    resp.status_code = status
    resp.json = MagicMock(return_value=payload)
    if status >= 400:
        resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                f"status {status}", request=MagicMock(), response=resp
            )
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _client(*, response=None, error=None):
    """Двойник клиента: либо отдаёт ответ, либо роняет обращение."""
    client = MagicMock()
    client.get = AsyncMock(
        side_effect=error) if error is not None else AsyncMock(
        return_value=response)
    return client


def _settings(url: str = "http://loki:3100"):
    settings = MagicMock()
    settings.loki_url = url
    return settings


# =============================================================================
# Разбор успешного ответа
# =============================================================================


@pytest.mark.asyncio
async def test_a_successful_answer_parses_into_lines_newest_first():
    """Момент, уровень, источник и текст — и порядок от свежих к старым.

    Порядок несущий: администратор открывает журнал ради ПОСЛЕДНЕГО, что
    случилось, и перевёрнутая лента заставила бы его листать до конца ровно там,
    где счёт идёт на секунды.
    """
    older = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)
    newer = datetime(2026, 8, 22, 10, 5, 0, tzinfo=timezone.utc)
    payload = _payload(
        _stream(
            {"container_name": "web-broadcaster", "level": "error"},
            [[_ns(older), "старая беда"]],
        ),
        _stream(
            {"account_id": "42", "level": "warn"},
            [[_ns(newer), "свежая беда"]],
        ),
    )

    with patch(
        "app.services.loki_client._client",
        return_value=_client(response=_response(payload)),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is False
    assert [line.text for line in window.lines] == ["свежая беда", "старая беда"]
    assert window.lines[0].at == newer
    assert window.lines[0].level == "warn"
    assert window.lines[0].source == "42"
    assert window.lines[1].source == "web-broadcaster"


@pytest.mark.asyncio
async def test_an_empty_but_healthy_answer_is_not_unavailable():
    """«Логов не было» и «источника нет» различимы ПО РЕЗУЛЬТАТУ, а не по длине.

    Оба состояния дают пустой перечень строк, и это ровно та пара, которую
    разметка обязана нарисовать по-разному: одно означает «за окно тихо»,
    другое — «мы не знаем, что было». Слитые в одно, они отвечают «ошибок нет»
    на вопрос, который задан именно потому, что что-то сломалось.
    """
    with patch(
        "app.services.loki_client._client",
        return_value=_client(response=_response(_payload())),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.lines == []
    assert window.unavailable is False
    assert window.capped is False


# =============================================================================
# Недоступность источника — одна ветка на три причины
# =============================================================================


@pytest.mark.asyncio
async def test_a_refused_connection_is_reported_unavailable_and_does_not_raise():
    """Мониторинг опционален (D-28), значит его отсутствие — не исключение.

    Исключение наружу здесь означало бы пятисотку на подразделе, который
    открывают ИМЕННО в аварии: администратор потерял бы и логи, и подраздел
    разом.
    """
    with patch(
        "app.services.loki_client._client",
        return_value=_client(error=httpx.ConnectError("nope")),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is True
    assert window.lines == []
    assert window.capped is False


@pytest.mark.asyncio
async def test_an_expired_timeout_is_the_same_unavailable_and_leaves_a_named_line():
    """Истёкший таймаут ведёт в ТУ ЖЕ ветку и оставляет именованный след.

    Медленный источник на пути синхронного рендера — отказ в обслуживании
    подразделу (T-06-LOG1): без явного предела ожидания страница висела бы
    столько, сколько молчит внешняя служба. След в журнале приложения нужен
    затем, чтобы «плашка вместо логов» имела причину, читаемую снаружи экрана:
    текст стороннего исключения на экран не выходит.
    """
    with patch(
        "app.services.loki_client._client",
        return_value=_client(error=httpx.ReadTimeout("slow")),
    ), patch(
        "app.services.loki_client.get_settings", return_value=_settings()
    ), patch("app.services.loki_client.logger") as log:
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is True
    (event,), fields = log.warning.call_args
    assert event == "loki_unavailable"
    assert "error" in fields


@pytest.mark.asyncio
async def test_an_error_status_from_the_source_is_unavailable_not_an_empty_answer():
    """Код ошибки источника — недоступность, а не пустая выдача.

    Источник, ответивший пятисоткой, не сообщил «строк нет»: он не сообщил
    ничего. Приняв его отказ за пустую выдачу, подраздел выдал бы догадку за
    измерение.
    """
    with patch(
        "app.services.loki_client._client",
        return_value=_client(response=_response({}, status=503)),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is True
    assert window.lines == []


@pytest.mark.asyncio
async def test_a_missing_client_is_unavailable_rather_than_an_exception():
    """Клиент не собрался — тот же штатный отказ, а не падение обработчика."""
    with patch(
        "app.services.loki_client._client", return_value=None
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is True
    assert window.lines == []


# =============================================================================
# Потолок: обе стороны границы
# =============================================================================


@pytest.mark.asyncio
async def test_more_lines_than_the_cap_come_back_capped_and_truncated():
    """Усечение НАЗЫВАЕТСЯ признаком, а предел выдачи — потолок ПЛЮС ОДИН.

    Единица сверх потолка не печатается: она и есть улика. Запрошенный предел
    ровно в потолок сделал бы «прочитано 200» неотличимым от «за окно 200», и
    признак пришлось бы выводить из длины — то есть объявлять полный перечень
    усечённым.
    """
    base = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)
    values = [
        [_ns(base + timedelta(seconds=n)), f"строка {n}"]
        for n in range(LOG_LINE_CAP + 7)
    ]
    payload = _payload(_stream({"container_name": "web", "level": "info"}, values))
    client = _client(response=_response(payload))

    with patch(
        "app.services.loki_client._client", return_value=client
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.capped is True
    assert len(window.lines) == LOG_LINE_CAP
    assert int(client.get.call_args.kwargs["params"]["limit"]) == LOG_LINE_CAP + 1


@pytest.mark.asyncio
async def test_exactly_the_cap_is_not_reported_capped():
    """Граница проверяется отдельным случаем: ровно потолок — это НЕ усечение.

    Признак «строго больше» и признак «не меньше» различаются ровно одним этим
    случаем, и он же — единственный, где ошибка была бы видна: полный перечень
    из двухсот строк объявил бы себя неполным.
    """
    base = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)
    values = [
        [_ns(base + timedelta(seconds=n)), f"строка {n}"]
        for n in range(LOG_LINE_CAP)
    ]
    payload = _payload(_stream({"container_name": "web", "level": "info"}, values))

    with patch(
        "app.services.loki_client._client",
        return_value=_client(response=_response(payload)),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.capped is False
    assert len(window.lines) == LOG_LINE_CAP


# =============================================================================
# Контракт запроса
# =============================================================================


@pytest.mark.asyncio
async def test_the_window_bounds_go_to_the_source_as_nanosecond_strings():
    """Наносекунды СТРОКОЙ — контракт запроса, а не оформление.

    Секунды или целое число вместо строки не роняют запрос: источник разберёт
    их как момент в далёком прошлом и вернёт пустоту — то есть ответит «логов
    нет» на исправный запрос. Ошибка этого класса неотличима от тишины.
    """
    client = _client(response=_response(_payload()))

    with patch(
        "app.services.loki_client._client", return_value=client
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        await query_range('{job="docker"}', timedelta(minutes=15))

    params = client.get.call_args.kwargs["params"]
    assert isinstance(params["start"], str)
    assert isinstance(params["end"], str)
    assert int(params["end"]) - int(params["start"]) == int(
        timedelta(minutes=15).total_seconds() * 1e9
    )
    assert params["direction"] == "backward"
    assert params["query"] == '{job="docker"}'


@pytest.mark.asyncio
async def test_the_source_address_comes_from_settings_not_from_a_literal():
    """Адрес источника — настройка с умолчанием, а не литерал в вызове.

    Умолчание указывает на службу мониторинга в общей сети; переопределение —
    из окружения, без выката кода. Форма уже применена в проекте ко всем
    внешним адресам.
    """
    client = _client(response=_response(_payload()))

    with patch(
        "app.services.loki_client._client", return_value=client
    ), patch(
        "app.services.loki_client.get_settings",
        return_value=_settings("http://logs.example:9999"),
    ):
        await query_range('{job="docker"}', timedelta(hours=1))

    url = client.get.call_args.args[0]
    assert url.startswith("http://logs.example:9999")
    assert url.endswith("/loki/api/v1/query_range")


def test_the_timeout_is_declared_as_a_constant_and_is_short():
    """Предел ожидания объявлен числом и невелик: рендер синхронный.

    Медленный источник не имеет права держать страницу: подраздел рисуется в
    том же запросе, и ожидание внешней службы — это ожидание администратора.
    """
    assert isinstance(LOKI_TIMEOUT_SEC, (int, float))
    assert 0 < LOKI_TIMEOUT_SEC <= 5


def test_the_settings_field_for_the_source_address_has_a_default():
    """Поле настройки существует и имеет умолчание.

    Без умолчания отсутствие переменной окружения роняло бы сборку настроек —
    то есть весь веб-процесс, — ради опциональной службы.
    """
    from app.config import Settings

    assert "loki_url" in Settings.model_fields
    assert Settings.model_fields["loki_url"].default
