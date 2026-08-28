"""Сборка ответа с уведомлением: внеполосный блок и его приклейка к фрагменту.

ПОЧЕМУ ОТДЕЛЬНЫЙ ФАЙЛ, А НЕ ГРУППА В `test_shell.py`. Там живут утверждения о
ДОСТАВКЕ шелла — что человек, открывший страницу, получил области уведомления и
их признаки. Здесь — утверждения о СБОРКЕ ответа: что `respond()`, отдавая
фрагмент, дописывает к нему внеполосный блок, и что блок этот подменяет
СОДЕРЖИМОЕ области, а не её узел. Предметы разные, и смешанные в одном файле они
бы скрыли друг друга: зелёная доставка ничего не говорит о сборке, а зелёная
сборка — о том, что в документе есть куда приехать.

ПОЧЕМУ УТВЕРЖДЕНИЯ ИДУТ ПО НАСТОЯЩЕМУ ОТВЕТУ `respond()`, А НЕ ПО РЕНДЕРУ
ВКЛЮЧЕНИЯ. Рендер включения доказал бы, что шаблон собирается; предмет FOUND-06
другой — что собранный блок ДОЕХАЛ до тела ответа вместе с фрагментом. Между
этими двумя утверждениями лежит ровно та граница, которую план 08-01 оставил
незакрытой словами в докстринге `respond()`.
"""
import pytest
from fastapi.responses import HTMLResponse, Response
from starlette.requests import Request

from app.pages import notices
from app.pages.htmx import HX_REQUEST_HEADER, NOTICE_QUERY_KEY, respond

# Форма подмены СОДЕРЖИМОГО области — то, чего требует FOUND-06. Обе строки
# выписаны здесь целиком, а не собраны из идентификаторов: тест, склеивающий
# ожидание из тех же кусков, что и шаблон, согласился бы с любой их правкой.
#
# ⚠️ ЗАКРЫВАЮЩАЯ КАВЫЧКА В ПЕРВОЙ СТРОКЕ НЕСУЩАЯ. Без неё цель вежливой области
# была бы ПОДСТРОКОЙ цели настойчивой, и утверждение «цели вежливой в блоке
# нет» краснело бы там, где всё правильно.
POLITE_TARGET = 'hx-swap-oob="innerHTML:#notice"'
ASSERTIVE_TARGET = 'hx-swap-oob="innerHTML:#notice-alert"'

# Форма подмены УЗЛА. В областях уведомления она запрещена: узел, унесённый из
# документа, лишает цели ВСЕ последующие ответы, и молча.
NODE_SWAP = 'hx-swap-oob="true"'

# Тело фрагмента. Значение намеренно не похоже ни на разметку, ни на текст
# записи: утверждение «фрагмент доехал» обязано отличать его от всего остального.
FRAGMENT_BODY = "ROW"

# Адрес деградации. Любой локальный — предмет утверждений не он.
DEGRADED_PATH = "/history"


def _request(headers: dict[str, str] | None = None) -> Request:
    """Запрос без приложения — для утверждений о САМОЙ сборке ответа.

    Форма скопирована из `test_htmx_response_layer.py` дословно и по тому же
    основанию: `respond()` не трогает ни базу, ни маршруты, и прогонять его
    через собранное приложение значило бы ронять эти утверждения за компанию
    при поломке любого обработчика.
    """
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "server": ("test", 80),
            "path": "/",
            "root_path": "",
            "query_string": b"",
            "headers": [
                (name.lower().encode("latin-1"), value.encode("latin-1"))
                for name, value in (headers or {}).items()
            ],
        }
    )


def _htmx_request() -> Request:
    return _request({HX_REQUEST_HEADER: "true"})


def _fragment(body: str = FRAGMENT_BODY, media_type: str | None = None):
    """Фабрика фрагмента в той форме, которой её ждёт `respond()`."""

    async def build() -> Response:
        if media_type is None:
            return HTMLResponse(content=body)
        return Response(content=body, media_type=media_type)

    return build


def _exploding_fragment():
    """Фрагмент, само построение которого есть провал утверждения."""

    async def build() -> Response:  # pragma: no cover - вызов и есть отказ
        raise AssertionError(
            "фрагмент собран на запросе БЕЗ признака htmx — человек без "
            "JavaScript получил бы кусок разметки вместо страницы"
        )

    return build


async def _body_of(code: str | None, *, variant_check: str | None = None) -> str:
    """Тело ответа `respond()` на запросе htmx с фрагментом и данным кодом."""
    record = notices.notice_for(code) if code else None
    if variant_check is not None:
        assert record is not None and record.variant == variant_check, (
            f"код {code!r} перестал быть записью варианта {variant_check!r} — "
            "утверждение ниже проверяло бы не то, что называет"
        )
    response = await respond(
        _htmx_request(),
        redirect=DEGRADED_PATH,
        notice=code,
        fragment=_fragment(),
    )
    return response.body.decode("utf-8")


@pytest.mark.asyncio
async def test_a_fragment_answer_carries_the_notice_out_of_band():
    """Тело несёт И фрагмент, И внеполосный блок с текстом записи.

    Это несущее утверждение файла. До него `respond()` отдавал фрагмент как
    есть: человек, оставшийся на месте благодаря слою письма, узнавал исход
    своего действия ТОЛЬКО из самого фрагмента — то есть на 35 из 36
    обработчиков не узнавал никак.
    """
    record = notices.notice_for(notices.RETRY_QUEUED)
    assert record is not None

    response = await respond(
        _htmx_request(),
        redirect=DEGRADED_PATH,
        notice=notices.RETRY_QUEUED,
        fragment=_fragment(),
    )
    body = response.body.decode("utf-8")

    assert FRAGMENT_BODY in body, (
        "тело фрагмента пропало из ответа — приклейка не дописала блок, "
        "а заменила собой то, что собрал вызывающий"
    )
    assert record.text in body, (
        "внеполосного блока с текстом записи в теле нет — исход действия снова "
        "невидим тому, кто остался на странице"
    )

    # ⚠️ ДЛИНА ТЕЛА ОБЯЗАНА БЫТЬ ПЕРЕСЧИТАНА. Заголовок длины, оставшийся от
    # исходного фрагмента, обрезал бы дописанный блок ровно по прежней границе:
    # ответ пришёл бы усечённым, и увидеть это можно только по проводу, а не в
    # объекте ответа.
    assert int(response.headers["content-length"]) == len(response.body), (
        "заголовок длины тела не пересчитан после приклейки — по проводу "
        "уехало бы усечённое тело"
    )


@pytest.mark.asyncio
async def test_without_a_code_the_fragment_body_is_left_alone():
    """Без кода тело равно телу фрагмента ПОСИМВОЛЬНО.

    Утверждение о равенстве, а не о вхождении: приклейка, срабатывающая всегда,
    дописывала бы пустой блок в каждый фрагмент проекта — то есть меняла бы
    ответы там, где уведомления нет вовсе.
    """
    response = await respond(
        _htmx_request(),
        redirect=DEGRADED_PATH,
        notice=None,
        fragment=_fragment(),
    )

    assert response.body.decode("utf-8") == FRAGMENT_BODY, (
        "тело фрагмента изменилось при отсутствии кода уведомления"
    )


@pytest.mark.asyncio
async def test_the_out_of_band_block_replaces_content_and_not_the_node():
    """Блок объявляет подмену СОДЕРЖИМОГО области, а не её узла (T-08-21).

    Разница не косметическая. Подмена узла УНОСИТ область из документа и ставит
    на её место присланный узел; следующий ответ, целящийся по тому же
    идентификатору, попадёт уже не туда, а в худшем случае — никуда. Область
    уведомления живёт в шелле и обязана пережить любое число ответов.
    """
    body = await _body_of(notices.RETRY_QUEUED)

    assert POLITE_TARGET in body, (
        "внеполосный блок не объявляет подмену содержимого вежливой области"
    )
    assert NODE_SWAP not in body, (
        "внеполосный блок объявил подмену УЗЛА — область уведомления уедет из "
        "документа, и следующий ответ приземлится в никуда"
    )


@pytest.mark.asyncio
async def test_the_block_targets_the_assertive_region_for_an_error_record():
    """Вариант error целится в НАСТОЙЧИВУЮ область, и только в неё."""
    body = await _body_of(notices.PAYMENT_FAILED, variant_check="error")

    assert ASSERTIVE_TARGET in body, (
        "отказ не приехал в настойчивую область"
    )
    assert POLITE_TARGET not in body, (
        "тот же ответ целится ЕЩЁ И в вежливую область — плашка нарисуется "
        "дважды, а объявлена будет двумя разными тонами"
    )


@pytest.mark.asyncio
async def test_the_block_targets_the_polite_region_for_a_calm_record():
    """Остальные варианты целятся в ВЕЖЛИВУЮ область, и только в неё."""
    body = await _body_of(notices.RETRY_QUEUED, variant_check="success")

    assert POLITE_TARGET in body
    assert ASSERTIVE_TARGET not in body, (
        "успех приехал в настойчивую область — объявление перебило бы человека "
        "посреди чтения там, где перебивать нечем"
    )


@pytest.mark.asyncio
async def test_a_non_html_fragment_refuses_the_glue_instead_of_corrupting_it():
    """Фрагмент не-HTML: приклейка ОТКАЗЫВАЕТ, а не портит тело молча.

    Дописать разметку в тело иного типа означало бы отдать клиенту документ,
    который тот разбирает по объявленным правилам, — то есть сломать его без
    единого признака. Отказ громкий и на стороне разработчика.
    """
    with pytest.raises(ValueError):
        await respond(
            _htmx_request(),
            redirect=DEGRADED_PATH,
            notice=notices.RETRY_QUEUED,
            fragment=_fragment(body="{}", media_type="application/json"),
        )


@pytest.mark.asyncio
async def test_without_the_htmx_flag_the_fragment_is_never_built():
    """Без признака htmx фрагмент не собирается, а код едет АДРЕСОМ.

    Половина пары D-16, записанная здесь потому, что приклейка — это ветка
    фрагмента: помощник, начавший собирать фрагмент ради блока уведомления,
    отдал бы кусок разметки человеку без JavaScript.
    """
    response = await respond(
        _request(),
        redirect=DEGRADED_PATH,
        notice=notices.RETRY_QUEUED,
        fragment=_exploding_fragment(),
    )

    assert response.status_code == 302
    assert response.headers["location"] == (
        f"{DEGRADED_PATH}?{NOTICE_QUERY_KEY}={notices.RETRY_QUEUED}"
    ), (
        "код исхода не уехал адресом — приземлившаяся страница нарисует пустоту"
    )
