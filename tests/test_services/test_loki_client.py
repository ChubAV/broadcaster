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
async def test_unreadable_settings_are_the_same_unavailable_not_a_five_hundred():
    """Несобравшиеся настройки — та же недоступность, а не отказ подраздела.

    Сборка настроек читает окружение и падает, если обязательного поля в нём
    нет. Прочитанный ДО гарда адрес превращал бы это падение в пятисотку на
    подразделе — то есть отнимал бы и логи, и сам подраздел разом, ради службы,
    объявленной ОПЦИОНАЛЬНОЙ. «Адреса источника нет» означает ровно то же, что
    «источник не отвечает»: прочитать негде.

    Дефект был живым и пойман обходом шелла: подраздел отвечал 500 везде, где
    настройки собираются подменой зависимости, а не из окружения.
    """
    client = _client(response=_response(_payload()))

    with patch(
        "app.services.loki_client._client", return_value=client
    ), patch(
        "app.services.loki_client.get_settings",
        side_effect=ValueError("обязательное поле настроек отсутствует"),
    ):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is True
    assert window.lines == []
    client.get.assert_not_awaited()


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


# =============================================================================
# Задача 2: сборка запроса — словарь уровней на ДВА словаря источника
# =============================================================================
#
# ⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ЭТОГО РАЗДЕЛА — про чипс предупреждения. Уровень
# «предупреждение» приезжает в источник ДВУМЯ разными словами: журналирование
# приложения пишет одно (`structlog.stdlib.add_log_level` кладёт имя метода
# логгера в нижнем регистре), а сборщик логов ПЕРЕВОДИТ числовой уровень воркера
# канала WhatsApp шаблоном во второе (`monitoring/promtail.yml`). Селектор,
# собранный из одного слова, скрыл бы ровно половину предупреждений — молча, при
# статусе 200 и пустом перечне, неотличимом от отсутствия предупреждений. Тест
# перечисляет ОБА слова явными литералами: вывод их из самого словаря сделал бы
# утверждение тавтологией.
#
# ⚠️ ТЕКСТ ПОИСКА — ЕДИНСТВЕННЫЙ ВХОД ФАЗЫ, УХОДЯЩИЙ В ЧУЖОЙ ЯЗЫК ЗАПРОСОВ
# (T-06-LQL). Кавычка внутри него ломает запрос СИНТАКСИЧЕСКИ, и подраздел
# ответил бы отказом источника на нормальный пользовательский ввод. Утверждение
# адресовано ЦЕЛОСТНОСТИ собранного запроса, а не отсутствию символа: проверка
# «кавычки нет» зеленела бы и на молча выброшенном тексте.

from app.services.loki_client import (  # noqa: E402
    LEVEL_CHIPS,
    LOG_WINDOWS,
    LOG_WINDOW_DEFAULT,
    build_logql,
    clean_level,
    clean_source,
    clean_window,
)


def _line_filter_payload(query: str) -> str:
    """Содержимое фильтра строки, снятое РАЗБОРОМ, а не срезом по кавычке.

    Разбор идёт посимвольно с учётом экранирования и ТРЕБУЕТ, чтобы строка
    закрылась ровно в конце запроса. Именно это и означает «запрос остался
    синтаксически целым»: неэкранированная кавычка закрыла бы строку раньше, и
    хвост запроса оказался бы за её пределами.
    """
    marker = ' |= "'
    assert marker in query, f"фильтра строки нет вовсе: {query}"
    body = query[query.index(marker) + len(marker):]

    out = []
    escaped = False
    for pos, ch in enumerate(body):
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            assert pos == len(body) - 1, (
                "строка фильтра закрылась НЕ в конце запроса — значит кавычка "
                f"внутри текста не экранирована: {query}"
            )
            return "".join(out)
        out.append(ch)
    raise AssertionError(f"строка фильтра не закрыта вовсе: {query}")


def test_the_warning_level_chip_covers_both_words_the_source_receives():
    """Чипс предупреждения покрывает ОБА слова уровня, и оба названы явно.

    Приложение пишет `warning`, перевод числового уровня воркера канала
    WhatsApp даёт `warn`. Один литерал в селекторе скрыл бы ровно половину
    предупреждений — при статусе 200 и пустом списке, который читается как
    «предупреждений нет».
    """
    query = build_logql("warn", None, None)

    assert "warn" in LEVEL_CHIPS["warn"]
    assert "warning" in LEVEL_CHIPS["warn"]
    assert "level=~" in query, "условие уровня собрано равенством одному слову"
    assert '"warn|warning"' in query or '"warning|warn"' in query, query


def test_the_error_level_chip_covers_the_declared_set_not_a_single_word():
    """Ошибка тоже приезжает не одним словом: критическая и фатальная — тоже она.

    Администратор, отбирающий ошибки, ищет «что сломалось». Уровень выше
    ошибки — это тем более сломалось, и выпасть из отбора он не имеет права.
    """
    query = build_logql("error", None, None)

    assert set(LEVEL_CHIPS["error"]) >= {"error", "critical", "fatal"}
    for value in LEVEL_CHIPS["error"]:
        assert value in query, f"{value} не попал в селектор: {query}"


def test_the_all_level_chip_adds_no_level_condition_at_all():
    """Вариант «все» не добавляет условия по уровню вовсе.

    Не «пустой перечень значений», а отсутствие условия: селектор с пустым
    перечислением не совпал бы ни с одной строкой.
    """
    query = build_logql("", None, None)

    assert "level" not in query, query


def test_a_level_outside_the_declared_dictionary_falls_back_to_all():
    """Мусорный уровень означает «все», а не подставляется в запрос сырым.

    Значение приезжает строкой адреса, то есть из ссылки, закладки или чужого
    сообщения. Подставленное сырым, оно ушло бы в чужой язык запросов; принятое
    за отбор — нарисовало бы администратору фильтр, которого он не задавал.
    """
    assert clean_level('error"} |= "') == ""
    query = build_logql('error"} |= "', None, None)

    assert "level" not in query, query
    assert "|=" not in query, query


def test_a_numeric_source_reads_as_an_account_id_and_a_name_as_a_container():
    """Форма значения различает воркер аккаунта и службу сборки.

    У воркера аккаунта есть метка идентификатора: имя его контейнера собирается
    менеджером и меняется при пересоздании, а идентификатор — нет. У служб
    сборки идентификатора не существует вовсе.
    """
    assert 'account_id="42"' in build_logql("", "42", None)
    assert 'container_name="web-broadcaster"' in build_logql(
        "", "web-broadcaster", None
    )


def test_a_source_outside_the_declared_vocabulary_is_dropped():
    """Источник санируется закрытым словарём ЛИБО формой идентификатора.

    Перечень служб объявлен на сервере, идентификаторы аккаунтов не
    перечислимы — но состоят только из цифр, и ничем иным быть не могут.
    Значение, не подходящее ни под то, ни под другое, фильтром не становится.
    """
    assert clean_source('web" ,x="') is None
    assert clean_source("nope-broadcaster") is None
    assert clean_source("42") == "42"
    assert clean_source("web-broadcaster") == "web-broadcaster"


def test_the_search_text_goes_to_the_line_filter_not_into_the_label_selector():
    """Текст уходит в фильтр СТРОКИ: селектор индексируется и текста не примет.

    Уехав в селектор, произвольный текст не нашёл бы ничего — при исправном на
    вид запросе.
    """
    query = build_logql("", None, "таймаут")

    selector = query.split(" |= ")[0]
    assert "таймаут" not in selector, query
    assert _line_filter_payload(query) == "таймаут"


def test_a_quote_inside_the_search_text_is_escaped_and_the_query_stays_whole():
    """Кавычка экранируется, и запрос остаётся синтаксически ЦЕЛЫМ.

    Утверждение адресовано целостности, а не отсутствию символа: проверка «в
    запросе нет кавычки» зеленела бы и на молча выброшенном тексте.
    """
    text = 'он сказал "готово"'
    query = build_logql("error", None, text)

    assert _line_filter_payload(query) == text
    assert query.startswith("{"), query


def test_a_backslash_inside_the_search_text_is_escaped():
    """Обратная косая экранируется ПЕРВОЙ, иначе она съедает свою же кавычку."""
    text = 'путь C:\\temp и кавычка "'
    query = build_logql("", None, text)

    assert _line_filter_payload(query) == text


def test_an_empty_search_text_adds_no_line_filter():
    """Пустой текст не добавляет фильтра строки вовсе.

    Фильтр по пустой строке совпал бы со всем — то есть был бы бесполезен, — но
    в запросе выглядел бы как действующий отбор.
    """
    assert " |= " not in build_logql("", None, "")
    assert " |= " not in build_logql("", None, None)
    assert " |= " not in build_logql("", None, "   ")


def test_a_window_outside_the_declared_dictionary_falls_back_to_one_hour():
    """Окон ровно три, и мусорное значение заменяется умолчанием в час.

    Произвольного диапазона нет намеренно: срок хранения источника — семь
    суток, и произвольный диапазон уткнулся бы в него молча, вернув неполную
    выдачу без единого признака неполноты.
    """
    assert set(LOG_WINDOWS) == {"15m", "1h", "24h"}
    assert LOG_WINDOW_DEFAULT == "1h"
    assert clean_window("nope") == LOG_WINDOW_DEFAULT
    assert clean_window(None) == LOG_WINDOW_DEFAULT
    assert clean_window("15m") == "15m"
    assert LOG_WINDOWS[LOG_WINDOW_DEFAULT].delta == timedelta(hours=1)


# =============================================================================
# ОТВЕТ НЕВЕРНОЙ ФОРМЫ — ТА ЖЕ НЕДОСТУПНОСТЬ, А НЕ ПЯТИСОТКА (WR-03)
#
# ⚠️ ПОЧЕМУ ЭТО ОТДЕЛЬНЫЙ РАЗДЕЛ, А НЕ ЕЩЁ ОДИН СЛУЧАЙ К «недоступности».
# Утверждения выше проверяют, что МОЛЧАНИЕ источника — штатная ветка. Здесь
# проверяется соседнее и до ревизии не выполнявшееся: ответ, который ПРИШЁЛ, но
# устроен не так, как договаривались. Разбор содержимого жил снаружи всех
# гардов, и любая из четырёх поломок формы уносила подраздел в 500 через общий
# обработчик — то есть подраздел, написанный ради работы в аварии, отказывал от
# аварии.
# =============================================================================


MALFORMED_ANSWERS = {
    "result не перечень": {"status": "success", "data": {"result": 42}},
    "элемент перечня не словарь": {
        "status": "success",
        "data": {"result": ["не словарь"]},
    },
    "values не итерируемы": {
        "status": "success",
        "data": {"result": [{"stream": {}, "values": 7}]},
    },
    "запись короче двух полей": {
        "status": "success",
        "data": {"result": [{"stream": {}, "values": [["только момент"]]}]},
    },
    "момент не число": {
        "status": "success",
        "data": {"result": [{"stream": {}, "values": [["не момент", "текст"]]}]},
    },
    "момент вне календаря": {
        "status": "success",
        "data": {
            "result": [{"stream": {}, "values": [["9" * 30, "текст"]]}]
        },
    },
    "метки не словарь": {
        "status": "success",
        "data": {"result": [{"stream": ["не словарь"], "values": []}]},
    },
}


@pytest.mark.asyncio
@pytest.mark.parametrize("shape", sorted(MALFORMED_ANSWERS))
async def test_an_answer_of_the_wrong_shape_is_unavailable_not_an_exception(shape):
    """Ответ неверной формы = «прочитать негде», и НИ ОДНО исключение не выходит.

    ⚠️ УТВЕРЖДАЕТСЯ ИМЕННО ОТСУТСТВИЕ ИСКЛЮЧЕНИЯ, А НЕ ТОЛЬКО ПРИЗНАК. Прежний
    разбор не падал бы, если бы источник всегда отвечал по договорённости;
    предмет находки в том, что он ВЕРИЛ ответу. Вызов сам по себе, доехавший до
    возврата, и есть половина утверждения.

    Пустой перечень строк здесь недостаточен: он неотличим от «за окно ничего не
    было», и разметка, выводящая недоступность из длины, сказала бы
    администратору «ошибок нет» в самой аварии.
    """
    with patch(
        "app.services.loki_client._client",
        return_value=_client(response=_response(MALFORMED_ANSWERS[shape])),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is True, (
        f"{shape}: ответ неверной формы принят за здоровую пустоту — подраздел "
        "скажет «ошибок нет» ровно в аварии"
    )
    assert window.lines == []
    assert window.capped is False


@pytest.mark.asyncio
async def test_the_unreadable_answer_leaves_a_named_line_in_the_journal():
    """Форма, которой не договаривались, НАЗЫВАЕТСЯ в журнале одним ключом.

    Событие с точки зрения экрана — то же «прочитать негде», и различить
    «источник молчит» от «источник отвечает не тем» можно только в журнале.
    Без именованной записи причина не устанавливалась бы вовсе.
    """
    with patch(
        "app.services.loki_client._client",
        return_value=_client(
            response=_response(MALFORMED_ANSWERS["элемент перечня не словарь"])
        ),
    ), patch(
        "app.services.loki_client.get_settings", return_value=_settings()
    ), patch("app.services.loki_client.logger") as log:
        await query_range('{job="docker"}', timedelta(hours=1))

    events = [call.args[0] for call in log.warning.call_args_list if call.args]
    assert "loki_unreadable_answer" in events, (
        f"нечитаемый ответ не назван в журнале: {events}"
    )


@pytest.mark.asyncio
async def test_a_healthy_answer_still_parses_after_the_guard_moved():
    """ГРАНИЦА СВЕРХУ: гард, отвергающий ВСЁ, прошёл бы утверждения выше.

    Ветка «недоступно», накрывшая и здоровый ответ, оставила бы подраздел
    вечно пустым и вечно зелёным на всех случаях этого раздела.
    """
    moment = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    payload = _payload(
        _stream({"account_id": "7", "level": "error"}, [[_ns(moment), "упало"]])
    )

    with patch(
        "app.services.loki_client._client",
        return_value=_client(response=_response(payload)),
    ), patch("app.services.loki_client.get_settings", return_value=_settings()):
        window = await query_range('{job="docker"}', timedelta(hours=1))

    assert window.unavailable is False, (
        "здоровый ответ объявлен недоступностью — гард отвергает всё, и "
        "подраздел пуст навсегда"
    )
    assert [line.text for line in window.lines] == ["упало"]
