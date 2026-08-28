"""Слой ответа: отказ доезжает до человека ОБОИМИ путями, а не одним.

ПОЧЕМУ ЭТОТ ФАЙЛ СУЩЕСТВУЕТ. Отказ, отвечающий полной перезагрузке редиректом
на место, где чинят, при запросе htmx превращался в НИЧТО: слой письма получает
302, следует ему незаметно и подставляет в область свопа целый документ — или,
при закрытом свопе, не подставляет ничего. Человек в обоих случаях остаётся на
прежнем экране без единого слова о том, что действие отвергнуто. Утверждения
ниже пишутся ПАРАМИ (D-16) именно поэтому: одиночное утверждение о редиректе
зеленело бы ровно в том состоянии продукта, которое фаза и чинит.

ЧТО ИМЕННО УТВЕРЖДАЕТ ВТОРАЯ ПОЛОВИНА ПАРЫ. Не только «пришёл заголовок
перехода», но и «в теле НЕТ документа и НЕТ машинного `detail`». Эти две строки
закрывают обе сегодняшние формы невидимого отказа сразу: подставленный в область
свопа целый HTML-документ и тело `{"detail": …}`, которое отдаёт `HTTPException`
при любом статусе, включая 2xx.

ФОРМА ОТКАЗА БЕЗ htmx СОХРАНЯЕТСЯ ДОСЛОВНО, И ЭТО ПРЕДМЕТ, А НЕ ФОН. Фаза
меняет ТРАНСПОРТ отказа и не имеет права изменить ни предикат, по которому отказ
принимается, ни ответ тому, кто пришёл без слоя письма (FOUND-04). Первая
половина каждой пары стережёт ровно это.
"""
import inspect
import sys
import types

import pytest
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.pages.htmx import (
    HX_REQUEST_HEADER,
    NOTICE_QUERY_KEY,
    HtmxRefusal,
    is_htmx,
    location_response,
    refuse,
    respond,
)
# Помощники входа под чужой личностью берутся ИМПОРТОМ, а не второй копией.
# `_enter` УДОСТОВЕРЯЕТСЯ, что вход состоялся: без этой проверки утверждения о
# «действии под чужой личностью» зеленели бы на обычной админской сессии, ничего
# не проверяя, — и вторая копия помощника рано или поздно её потеряла бы. Та же
# доктрина единственного источника, по которой `test_htmx_response_contract.py`
# импортирует разборщик конфигурации, а не переписывает его.
from tests.test_pages.test_impersonation import (
    IMPERSONATION_REFUSAL_MARK,
    _detail_of,
    _enter,
    _seed_target,
)

# Адрес отказа гейта доступа. Выписан здесь строкой, а не импортирован из
# проверяемого модуля: тест, берущий ожидание из предмета проверки, согласился
# бы с любой его правкой — та же доктрина, по которой `test_access_gate.py`
# держит `EXPIRED_LOCATION` своей строкой.
ACCESS_EXPIRED_LOCATION = "/billing?expired=1"

# Страница, создающая ценность, — то есть закрываемая истёкшим доступом.
CLOSED_PAGE = "/ads"

# Адрес, на который уводит отвергнутое действие под чужой личностью. Выписан
# строкой по тому же основанию, что и адрес выше: ожидание, взятое из предмета
# проверки, согласилось бы с любой его правкой.
IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"


def _request(headers: dict[str, str] | None = None) -> Request:
    """Запрос без приложения — для утверждений о САМОМ слое ответа.

    Помощники слоя (`is_htmx`, `location_response`, `refuse`) не трогают ни базу,
    ни маршруты, и прогонять их через собранное приложение значило бы уронить эти
    утверждения за компанию при поломке любого обработчика. Поведение маршрутов
    проверяется отдельно — парами выше.
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


# --- Пара 1: отказ гейта доступа ---------------------------------------------


@pytest.mark.asyncio
async def test_a_closed_route_answers_a_full_reload_with_a_redirect(
    expired_client: AsyncClient,
):
    """Человек без слоя письма получает ТОТ ЖЕ ответ, что и до фазы.

    Утверждение стоит первым в паре, потому что оно — про сохранность, а не про
    новизну: базовый путь обязан остаться нетронутым, иначе улучшение одного
    транспорта оплачено поломкой другого.
    """
    response = await expired_client.get(CLOSED_PAGE, follow_redirects=False)

    assert response.status_code == 302, (
        f"закрытая страница ответила {response.status_code} на полную "
        "перезагрузку — форма отказа без htmx изменилась"
    )
    assert response.headers["location"] == ACCESS_EXPIRED_LOCATION, (
        f"редирект ведёт на {response.headers.get('location')!r}, а человек с "
        "истёкшим доступом обязан попасть туда, где чинят"
    )


@pytest.mark.asyncio
async def test_a_closed_route_answers_htmx_with_a_location_header(
    expired_client: AsyncClient, htmx_client: AsyncClient,
):
    """Человек со слоем письма УЗНАЁТ об отказе, а не остаётся на прежнем экране.

    ⚠️ ДВЕ ФИКСТУРЫ ЗДЕСЬ — ОДИН КЛИЕНТ. `expired_client` состаривает подписку и
    оставляет cookie, `htmx_client` добавляет тому же объекту признак запроса
    htmx; порядок в сигнатуре и есть порядок применения.
    """
    response = await htmx_client.get(CLOSED_PAGE)

    assert response.status_code == 204, (
        f"закрытая страница ответила {response.status_code} на запрос htmx — "
        "у 204 тела нет ПО ОПРЕДЕЛЕНИЮ, и только этим статусом «не JSON» "
        "становится свойством ответа, а не обещанием кода"
    )
    assert response.headers.get("HX-Location") == ACCESS_EXPIRED_LOCATION, (
        "ответ не несёт заголовка перехода — браузер оставит человека на "
        "прежнем экране, ничего ему не сказав"
    )
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ — слой письма подставит его в область "
        "свопа, и вместо перехода человек получит страницу внутри страницы"
    )
    assert "detail" not in response.text, (
        "в теле приехал машинный `detail` — ровно та форма, которую FOUND-07 "
        "запрещает наравне с редиректом"
    )
    assert response.text == "", "у ответа 204 тела быть не может"


@pytest.mark.asyncio
async def test_the_header_alone_does_not_change_an_open_route(
    authed_client: AsyncClient, htmx_client: AsyncClient,
):
    """Признак запроса htmx САМ ПО СЕБЕ поведения маршрута не меняет.

    Без этого утверждения фикстура `htmx_client` была бы неотличима от «фикстуры,
    которая что-то ломает»: любой красный тест с ней списывался бы на заголовок.
    """
    response = await htmx_client.get(CLOSED_PAGE)

    assert response.status_code == 200, (
        f"открытая страница ответила {response.status_code} на запрос htmx — "
        "заголовок изменил поведение там, где ветки htmx нет вовсе"
    )
    assert "<!DOCTYPE" in response.text, (
        "открытая страница перестала отдавать документ"
    )


# --- Сам слой ответа ----------------------------------------------------------


def test_the_htmx_flag_is_read_from_the_request_header():
    """Признак читается ОДНИМ местом, и читается он предсказуемо.

    Пустое значение считается ОТСУТСТВИЕМ признака сознательно: заголовок с
    пустым значением слой письма не присылает никогда, а «пустая строка есть
    признак» означало бы, что ветку htmx включает запрос, ничего о ней не
    сказавший.
    """
    assert is_htmx(_request({HX_REQUEST_HEADER: "true"})) is True
    assert is_htmx(_request({HX_REQUEST_HEADER: "anything"})) is True
    assert is_htmx(_request()) is False
    assert is_htmx(_request({HX_REQUEST_HEADER: ""})) is False


def test_a_location_header_never_carries_a_foreign_or_unencodable_address():
    """Значение заголовка перехода — ЛОКАЛЬНЫЙ ASCII-путь, и ничто иное.

    Три угрозы закрываются одной проверкой (T-08-01, T-08-02, T-08-05): чужой
    адрес в заголовке перехода есть готовый открытый редирект; перевод строки в
    значении есть инъекция заголовка; кириллица в значении роняет кодирование
    заголовков в latin-1 и превращает отказ в 500.
    """
    for hostile in (
        "http://evil.example/x",   # схема — уводит с сайта
        "//evil.example/x",        # протокол-относительный — уводит так же
        "/billing?msg=Оплатите",   # не-ASCII — падение на кодировании
        "/x\r\nSet-Cookie: a=b",   # перевод строки — инъекция заголовка
        "/x\\y",                   # обратная косая — разбирается браузерами
        "billing",                 # не путь вовсе
        "",                        # пусто
    ):
        with pytest.raises(ValueError):
            location_response(hostile)


def test_a_location_response_carries_no_body_at_all():
    """Ответ перехода отдаёт ЗАГОЛОВОК и не отдаёт тела ни при каких условиях."""
    response = location_response(ACCESS_EXPIRED_LOCATION)

    assert response.status_code == 204
    assert response.headers["HX-Location"] == ACCESS_EXPIRED_LOCATION
    assert response.body == b""


def test_the_refusal_keeps_its_own_form_for_a_request_without_htmx():
    """Помощник отказа МЕНЯЕТ ТРАНСПОРТ и не сочиняет форму отказа сам.

    Форма отказа приходит параметром, потому что сегодняшних форм две — 302 с
    заголовком `location` у гейта доступа и 403 с `detail` у запрета действий под
    чужой личностью, — и помощник, скроенный под одну, вторую переписал бы.
    """
    without_htmx = HTTPException(status_code=418, detail="прежняя форма")

    with pytest.raises(HTTPException) as raised:
        refuse(_request(), location="/x", without_htmx=without_htmx)

    assert raised.value is without_htmx, (
        "помощник подменил переданную форму отказа своей — форма отказа без "
        "htmx перестала быть собственностью вызывающего"
    )


def test_the_refusal_of_a_request_with_htmx_carries_the_location():
    """На запросе htmx отказ поднимается СВОИМ типом, а не `HTTPException`.

    Свой тип здесь вынужден: обработчик FastAPI для `HTTPException` отдаёт
    `JSONResponse` при ЛЮБОМ статусе, включая 2xx, — то есть тело `{"detail": …}`,
    прямо запрещённое FOUND-07.
    """
    with pytest.raises(HtmxRefusal) as raised:
        refuse(
            _request({HX_REQUEST_HEADER: "true"}),
            location=ACCESS_EXPIRED_LOCATION,
            without_htmx=HTTPException(status_code=302),
        )

    assert raised.value.location == ACCESS_EXPIRED_LOCATION
    assert not isinstance(raised.value, HTTPException), (
        "отказ поднят потомком `HTTPException` — его перехватит обработчик "
        "фреймворка и превратит в JSON раньше нашего"
    )


def test_the_refusal_takes_its_destination_by_keyword_only():
    """Адрес отказа нельзя подать позиционно — иначе он однажды съедет местами.

    У помощника два аргумента одного вида «куда/чем отказать»; позиционный вызов
    рано или поздно перепутал бы их местами, и отказ уехал бы на адрес, собранный
    из формы отказа.
    """
    parameters = inspect.signature(refuse).parameters
    assert parameters["location"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["without_htmx"].kind is inspect.Parameter.KEYWORD_ONLY


# --- Пара 2: отказ действию под чужой личностью -------------------------------


@pytest.mark.asyncio
async def test_an_impersonated_action_answers_a_full_reload_with_its_own_refusal(
    admin_client: AsyncClient, db_session: AsyncSession,
):
    """Форма отказа под чужой личностью СВОЯ, и она сохраняется дословно.

    Отказ по чужой личности обязан отличаться от отказа по правам: администратор,
    получивший «нет прав» там, где мешает чужая личность, пойдёт чинить ПРАВА, а
    единственное нужное ему действие — выйти из чужой учётной записи — не было бы
    названо ни одним словом. Транспорт отказа меняется, различимость причин — нет.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    response = await admin_client.post(
        "/profile", data={"timezone": "Europe/Moscow"}, follow_redirects=False
    )

    assert response.status_code == 403, (
        f"форма профиля ответила {response.status_code} под чужой личностью — "
        "форма отказа без htmx изменилась"
    )
    assert IMPERSONATION_REFUSAL_MARK in _detail_of(response), (
        f"отказ не назвал причиной чужую личность: {_detail_of(response)!r}"
    )


@pytest.mark.asyncio
async def test_an_impersonated_action_answers_htmx_with_a_location_header(
    admin_client: AsyncClient, db_session: AsyncSession, htmx_client: AsyncClient,
):
    """Отвергнутое действие УВОДИТ на экран, где отказ будет виден и объяснён.

    ⚠️ АДРЕС ПЕРЕХОДА GET-СОВМЕСТИМЫЙ И НЕ РАВЕН ПУТИ ОТВЕРГНУТОГО ДЕЙСТВИЯ.
    Отвергается ЗАПИСЬ, и вернуть человека на её собственный путь нельзя — тот
    принимает только POST. Домашний экран той личности, под которой работает
    администратор, выбран потому, что именно там видна полоса возврата в
    администратора, то есть выход из положения, а не только его название.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    response = await htmx_client.post(
        "/profile", data={"timezone": "Europe/Moscow"}
    )

    assert response.status_code == 204, (
        f"форма профиля ответила {response.status_code} на запрос htmx"
    )
    assert response.headers.get("HX-Location") == IMPERSONATION_REFUSED_LOCATION, (
        "ответ не несёт заголовка перехода — человек остался на прежнем экране, "
        "а его правка тихо не сохранилась"
    )
    assert "detail" not in response.text, (
        "в теле приехал машинный `detail` — форма, запрещённая FOUND-07 наравне "
        "с редиректом"
    )
    assert "<!DOCTYPE" not in response.text, "в теле приехал целый документ"


@pytest.mark.asyncio
async def test_a_request_without_an_actor_is_refused_on_neither_transport(
    authed_client: AsyncClient, htmx_client: AsyncClient,
):
    """ГРАНИЦА «ОТСУТСТВИЕ ДЕЙСТВУЮЩЕГО ЛИЦА — НЕ ОТКАЗ» НЕ СДВИНУЛАСЬ.

    Запрет, срабатывающий ВСЕГДА, прошёл бы обе половины пары выше и при этом
    закрыл бы обычному пользователю правку собственного профиля. Предикат отказа
    вычисляется ДО развилки транспорта, поэтому новый транспорт не имеет права
    расширить множество отвергаемых ни на один запрос.
    """
    response = await htmx_client.post(
        "/profile", data={"timezone": "Europe/Moscow"}
    )

    assert "HX-Location" not in response.headers, (
        "обычный пользователь получил заголовок перехода — запрет сработал там, "
        "где действующего лица нет вовсе"
    )
    assert response.status_code == 200, (
        f"правка собственного профиля ответила {response.status_code} — запрет "
        "закрыл её обычному пользователю"
    )


@pytest.mark.asyncio
async def test_a_machine_receiver_without_a_token_is_refused_on_neither_transport(
    client: AsyncClient,
):
    """Уведомление о СОСТОЯВШЕМСЯ платеже новым транспортом тоже не задевается.

    Единственный вход денежного роутера приходит не от браузера и токена не
    несёт; отказ ему означал бы потерю уведомления о деньгах, которые УЖЕ
    заплачены, а такая потеря откатом кода не возвращается (D-53). Утверждение
    написано ОТ ПРОТИВНОГО: собственный гард вебхука отвечать отказом вправе —
    предмет в том, что отказ пришёл не от запрета чужой личности.
    """
    response = await client.post(
        "/api/billing/webhook",
        json={"event": "payment.succeeded", "object": {"id": "x"}},
    )

    assert "HX-Location" not in response.headers, (
        "вебхук отвергнут запретом чужой личности новым транспортом"
    )
    assert IMPERSONATION_REFUSAL_MARK not in _detail_of(response), (
        f"вебхук отвергнут запретом чужой личности: {_detail_of(response)!r}"
    )


# --- Главный выход обработчика ------------------------------------------------

# Код исхода действия, ЗАРЕГИСТРИРОВАННЫЙ в реестре уведомлений.
KNOWN_NOTICE = "profile_saved"
UNKNOWN_NOTICE = "нет-такого-кода"


@pytest.fixture
def notice_registry():
    """Реестр кодов уведомлений — настоящий, а при его отсутствии подменный.

    ⚠️ РЕЕСТР ЗАВОДИТСЯ СОСЕДНИМ ПЛАНОМ ТОЙ ЖЕ ВОЛНЫ (08-02), И ЭТИ УТВЕРЖДЕНИЯ
    ОБЯЗАНЫ БЫТЬ ПРОВЕРЯЕМЫ ДО ЕГО ПОЯВЛЕНИЯ. Предмет здесь — не содержимое
    реестра, а ДОГОВОР главного выхода с ним: код сверяется на СТОРОНЕ ЗАПИСИ, и
    незнакомый код останавливает ответ ошибкой программиста, а не доезжает до
    отрисовки. Договор проверяется одинаково на подменном и на настоящем
    реестре, поэтому фикстура молча уступает настоящему, как только тот появится.

    Пропустить утверждение до появления реестра было бы хуже некуда: невыполненная
    проверка выглядит в отчёте так же, как выполненная.
    """
    try:
        import app.pages.notices  # noqa: F401
    except ModuleNotFoundError:
        stand_in = types.ModuleType("app.pages.notices")
        stand_in.notice_for = lambda code: (
            ("Настройки сохранены.", "success") if code == KNOWN_NOTICE else None
        )
        sys.modules["app.pages.notices"] = stand_in
        try:
            yield stand_in
        finally:
            sys.modules.pop("app.pages.notices", None)
    else:
        yield sys.modules["app.pages.notices"]


def test_the_handler_exit_cannot_be_called_without_a_degraded_path():
    """ОБРАБОТЧИК БЕЗ ПУТИ ДЕГРАДАЦИИ НЕ СОБИРАЕТСЯ КАК ВЫЗОВ (FOUND-04).

    Это несущее свойство сигнатуры, а не соглашение: «не забудьте про базовый
    путь» соблюдается ровно до первого спешащего человека, а обязательный
    аргумент нельзя забыть в принципе — вызов просто не состоится. Ключевой
    аргумент (а не позиционный) выбран затем, чтобы адрес деградации нельзя было
    подать «случайно, третьим по счёту».
    """
    parameters = inspect.signature(respond).parameters

    assert parameters["redirect"].kind is inspect.Parameter.KEYWORD_ONLY, (
        "адрес деградации можно подать позиционно — однажды он съедет местами "
        "с соседним аргументом"
    )
    assert parameters["redirect"].default is inspect.Parameter.empty, (
        "у адреса деградации появилось умолчание — забыть про базовый путь "
        "снова стало возможно"
    )

    with pytest.raises(TypeError):
        respond(_request())


@pytest.mark.asyncio
async def test_a_full_reload_gets_a_redirect_with_the_outcome_in_the_address():
    """Без слоя письма исход действия едет АДРЕСОМ — как и до этой фазы."""
    bare = await respond(_request(), redirect="/profile")

    assert bare.status_code == 302
    assert bare.headers["location"] == "/profile"


@pytest.mark.asyncio
async def test_the_outcome_code_is_appended_to_the_degraded_address(notice_registry):
    """Код исхода приклеивается к адресу, а не подменяет его строку запроса.

    Второй «?» в адресе превратил бы код в часть значения соседнего параметра, и
    приземлившаяся страница не нарисовала бы плашку, ничего об этом не сказав.
    """
    plain = await respond(_request(), redirect="/profile", notice=KNOWN_NOTICE)
    assert plain.headers["location"] == f"/profile?{NOTICE_QUERY_KEY}={KNOWN_NOTICE}"

    with_query = await respond(
        _request(), redirect="/ads/5/edit?tab=schedule", notice=KNOWN_NOTICE
    )
    assert with_query.headers["location"] == (
        f"/ads/5/edit?tab=schedule&{NOTICE_QUERY_KEY}={KNOWN_NOTICE}"
    )


@pytest.mark.asyncio
async def test_htmx_without_a_fragment_gets_the_same_address_in_a_header(
    notice_registry,
):
    """Один и тот же адрес — два транспорта, и плашку рисует ОДИН путь (D-12).

    Код исхода едет АДРЕСОМ и на этом транспорте тоже. Поэтому приземлившаяся
    страница рисует плашку тем же кодом, что и после полной перезагрузки: второй
    механизм отрисовки не заводится и разойтись с первым не может.
    """
    response = await respond(
        _request({HX_REQUEST_HEADER: "true"}), redirect="/profile", notice=KNOWN_NOTICE
    )

    assert response.status_code == 204
    assert response.headers["HX-Location"] == (
        f"/profile?{NOTICE_QUERY_KEY}={KNOWN_NOTICE}"
    )
    assert response.body == b""


@pytest.mark.asyncio
async def test_htmx_with_a_fragment_gets_the_fragment_and_not_a_document():
    """Фрагмент отдаётся как есть: оболочка страницы НЕ перерисовывается."""

    async def fragment():
        return HTMLResponse("<span>сохранено</span>", status_code=200)

    response = await respond(
        _request({HX_REQUEST_HEADER: "true"}), redirect="/profile", fragment=fragment
    )

    assert response.status_code == 200
    assert response.body.decode() == "<span>сохранено</span>"
    assert "<!DOCTYPE" not in response.body.decode()


@pytest.mark.asyncio
async def test_an_unregistered_outcome_code_is_refused_on_the_writing_side(
    notice_registry,
):
    """Закрытое множество кодов стережётся НА СТОРОНЕ ЗАПИСИ, а не только рисования.

    Отрисовка по незнакомому коду не рисует ничего — то есть исход действия
    ПРОПАДАЕТ молча, и обнаруживается это жалобой. Ошибка на стороне записи
    ловит опечатку там, где её ещё можно исправить: в исходнике обработчика.
    """
    for hostile in (UNKNOWN_NOTICE, "", "profile_saved "):
        with pytest.raises(ValueError):
            await respond(_request(), redirect="/profile", notice=hostile)


@pytest.mark.asyncio
async def test_an_external_address_never_reaches_the_degraded_path():
    """Внешний адрес не проходит ни одним транспортом (T-08-05, ловушка Фазы 11).

    Внешний переход есть предмет отдельного заголовка и отдельной ветки, и
    вводит их Фаза 11 вместе с формой оплаты. До тех пор внешний адрес,
    поданный сюда по невнимательности, обязан не уехать никуда.
    """
    for hostile in ("https://yookassa.ru/pay/x", "//yookassa.ru/pay/x"):
        with pytest.raises(ValueError):
            await respond(_request({HX_REQUEST_HEADER: "true"}), redirect=hostile)
        with pytest.raises(ValueError):
            await respond(_request(), redirect=hostile)
