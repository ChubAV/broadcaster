"""Загрузка изображения объявления: фрагмент полосы вместо JSON (FETCH-01).

Форма файла взята у `tests/test_pages/test_account_groups.py:516-550` — пара
клиентов `authed_client` / `htmx_client` и адресное сообщение в каждом `assert`,
объясняющее, ЧТО увидит человек, а не повторяющее выражение.

⚠️ ИМЯ ФАЙЛОВОГО ПОЛЯ НАЗВАНО ЗДЕСЬ ЛИТЕРАЛОМ, И ЭТО НЕ ВТОРОЕ ОБЪЯВЛЕНИЕ ИМЕНИ.
Единственное объявление живёт в `app/services/image_upload.py`
(`UPLOAD_FILE_FIELD`), а разметка печатает его значением из контекста шаблона.
Тест же проверяет КОНТРАКТ запроса: ввезённая константа утверждала бы имя саму о
себе и позеленела бы при любом её переименовании — то есть ровно тогда, когда
браузер, посылающий старое имя, получил бы отказ. Имя `images` при этом
запрещено (WR-03): обработчик сохранения отвергает файловые части под ним
осознанно.

⚠️ ЗАПИСЬ ОБЪЕКТА ПОДМЕНЯЕТСЯ ПО АДРЕСУ `app.services.image_upload.upload_file_to_s3`.
Цель патча привязана к ИМЕНИ МОДУЛЯ, и промах даёт `AttributeError`, а не
осмысленный отказ (G-8) — переезд имени обязан ронять этот файл вслух.
"""

import io
import re
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.user import User

# Имя файлового поля составного запроса — см. абзац в шапке модуля.
UPLOAD_FIELD = "files"

# Форма ключа объекта: префикс пользователя, шестнадцатеричный токен, имя.
# Образец повторяет `_IMAGE_KEY_PATTERN` из `app/services/image_keys.py` по
# СМЫСЛУ, а не импортом: здесь проверяется, что маршрут выдал ключ ТОЙ формы,
# которую правило владения примет при следующем сохранении объявления.
IMAGE_KEY = re.compile(r"[1-9][0-9]*/[0-9a-f]{32}_[A-Za-z0-9._-]{1,100}")

# Скрытое поле ключа во фрагменте полосы. Атрибут `form="ad-form"` — буква
# критерия 1: полоса лежит ВНЕ формы объявления, и связь элемента с формой по
# атрибуту есть тот самый механизм, на котором уже держится кнопка «Сохранить».
HIDDEN_KEY_FIELD = re.compile(
    r'<input type="hidden" name="images" value="([^"]+)" form="ad-form">'
)

# Строка отказа во фрагменте полосы: у КАЖДОГО отвергнутого файла своя (D-05).
# Разбор строкой, а не разборщиком HTML: новой зависимости ради одного абзаца в
# суите не заводится — тот же приём применяют соседние файлы тестов страниц.
REFUSAL_ROW = re.compile(
    r'<p class="alert alert--error" role="alert">(.*?)</p>', re.DOTALL
)

# Заголовок события ответа и имя события. Оба названы ЛИТЕРАЛАМИ по тому же
# основанию, что и имя файлового поля выше: тест проверяет КОНТРАКТ, который
# получает браузер, а ввезённая из приложения константа утверждала бы имя саму о
# себе и зеленела бы ровно тогда, когда разметка со старым именем перестала бы
# слушать. Значение ASCII: кириллица в значении заголовка роняет ответ
# пятисоткой, и запрет вехи на тосты через заголовок события адресован ТЕКСТАМ
# для человека, а не именам событий.
EVENT_HEADER = "HX-Trigger-After-Swap"
UPLOAD_EVENT = "ads-image-attached"

# Разделитель имени и причины в строке отказа. Имя нормализовано и потому не
# может содержать этого сочетания; причина — может, поэтому деление идёт по
# ПЕРВОМУ вхождению, а не по последнему.
NAME_REASON_SEPARATOR = " — "


def refusal_rows(html: str) -> list[tuple[str, str]]:
    """Строки отказа фрагмента парами «показанное имя, причина».

    Отказ БЕЗ имени файла (подделанный ключ вложения — отказ относится к ключу,
    а файла за ним нет) возвращается парой с пустым именем: разделителя в такой
    строке нет вовсе, и `partition` отдаёт весь текст правой частью.
    """
    rows: list[tuple[str, str]] = []
    for row in REFUSAL_ROW.findall(html):
        left, separator, right = row.partition(NAME_REASON_SEPARATOR)
        rows.append((left, right) if separator else ("", left))
    return rows


def _attr_value(html: str, anchor: str, attr: str) -> str:
    """Значение атрибута элемента, опознанного по подстроке `anchor`.

    Разбор строкой — тот же приём, что применяют соседние файлы тестов страниц
    (`tests/test_pages/test_ads_editor.py`): новой зависимости разбора HTML ради
    одного атрибута не заводится. Отсутствие элемента или атрибута поднимает
    ValueError — тест падает, а не молча меряет пустоту.
    """
    start = html.index(anchor)
    opened = html.index(f'{attr}="', start) + len(attr) + 2
    return html[opened : html.index('"', opened)]


def image_key(user_id: int, name: str = "photo.png") -> str:
    """Ключ вложения ровно той формы, которую выдаёт маршрут загрузки.

    Источник формы — `app/services/image_upload.py`: `{user_id}/{uuid4().hex}_{имя}`.
    Форма повторяется здесь по СМЫСЛУ, а не импортом: тест обязан присылать то,
    что присылает браузер, а не то, что приложение считает правильным.
    """
    return f"{user_id}/{uuid4().hex}_{name}"


# --- форма запроса к редактору объявления ------------------------------------
#
# Повторена ЗДЕСЬ ПО МЕСТУ, а не ввезена из модуля тестов редактора: тестовый
# модуль не библиотека, и импорт одного из другого связал бы два файла порядком
# сборки и превратил бы вспомогательную функцию в неявный публичный контракт
# (тот же довод записан в шапке построителей изображений ниже).
#
# Нужна форма затем, что одно из правил этого модуля сводит ДВА обработчика:
# ответ загрузки разбирается на скрытые поля, и ровно они уходят следующим
# запросом в редактор. Порознь оба обработчика зелены — теряется работа человека
# именно на стыке.
FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
HX_HEADERS = {**FORM_HEADERS, "HX-Request": "true"}


def form_body(
    title: str = "Осенний завоз",
    text: str = "Полный текст объявления про осенний завоз",
    images: list[str] | None = None,
) -> str:
    fields: list[tuple[str, str]] = [("title", title), ("text", text)]
    fields += [("images", value) for value in images or []]
    return urlencode(fields)


async def _seed_ad(
    db: AsyncSession, user_id: int, images: list[str] | None = None
) -> Ad:
    ad = Ad(
        user_id=user_id,
        title="Осенний завоз",
        text="Полный текст объявления про осенний завоз",
        images=images or [],
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    """Пользователь, под которым ходит `authed_client`.

    Нужен затем, что ключ вложения НЕСЁТ идентификатор владельца первым звеном:
    без настоящего идентификатора «свой» ключ неотличим от чужого, и проверка
    принадлежности зеленела бы на любом поведении сервера.
    """
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    return result.scalar_one()


# --- построители настоящих изображений ---------------------------------------
#
# Скопированы из суиты снятого JSON-входа загрузки намеренно, а не ввезены
# оттуда: тестовый модуль не библиотека, и импорт одного из другого связал бы
# два файла порядком сборки и превратил бы вспомогательную функцию в неявный
# публичный контракт (тот же довод был записан в самом источнике).
#
# ⚠️ ИСТОЧНИК НАЗВАН СЛОВАМИ, А НЕ ПУТЁМ С НОМЕРАМИ СТРОК (находка IN-01).
# Прежде здесь стоял типизированный путь к модулю тестов того входа; сам модуль
# снят планом 12-05 ЦЕЛИКОМ, и путь указывал в пустоту. Дословно он не
# набирается и летописью: приёмочный обход находки ищет снятое имя по дереву
# `tests/`, и упоминание удовлетворило бы обход само.
_TILE_EDGE = 64


def _real_image(size, mode="RGB"):
    """Картинка с изменяющимся содержимым: заливка сжимается почти в ноль."""
    width, height = size
    tile_size = (min(width, _TILE_EDGE), min(height, _TILE_EDGE))
    tile = Image.new(mode, tile_size)
    pixels = tile.load()
    for x in range(tile_size[0]):
        for y in range(tile_size[1]):
            value = ((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256)
            pixels[x, y] = value if mode == "RGB" else (*value, 255)

    image = Image.new(mode, size)
    for left in range(0, width, tile_size[0]):
        for top in range(0, height, tile_size[1]):
            image.paste(tile, (left, top))
    return image


def _encode(image, fmt, **kwargs) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **kwargs)
    return buffer.getvalue()


def make_real_png_with_alpha_bytes(size=(600, 400)) -> bytes:
    """PNG с настоящей альфой — по D-4 он остаётся PNG и после пережатия.

    Взят ИМЕННО он, а не PNG без альфы: последний уезжает в хранилище JPEG'ом, и
    ключ получил бы расширение `.jpg`. Утверждение о `.png` в тесте ниже — это
    утверждение о том, что расширение ключа описывает СОХРАНЁННЫЕ байты (P-5), и
    на входе без альфы оно проверяло бы не то, что утверждает.
    """
    image = _real_image(size, mode="RGBA")
    image.putpixel((0, 0), (255, 255, 255, 0))
    return _encode(image, "PNG")


def make_webp_bytes() -> bytes:
    """Байты WebP: ``RIFF``, четыре байта размера, затем ``WEBP``.

    Скопировано из суиты снятого JSON-входа по тому же основанию, по которому
    скопированы построители выше: тестовый модуль не библиотека. Настоящим
    изображением байты быть не обязаны — распознавание идёт по первым байтам и
    отвергает формат ДО того, как до содержимого дойдёт декодер.
    """
    return b"RIFF" + b"\x24\x00\x00\x00" + b"WEBP" + b"VP8 " + b"\x00" * 16


# Вектор CR-02: SVG — тоже «изображение», но исполняемое. Отданный браузеру с
# origin хранилища, он выполняет свой скрипт в его контексте. Байты остаются
# заведомо корректным SVG: иначе утверждение мерило бы отказ дефектному файлу
# вместо отказа безупречному.
SVG_BYTES = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
    b"<script>alert(1)</script></svg>"
)


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_one_image_over_htmx_returns_the_strip_fragment(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Годная картинка с признаком htmx возвращает ФРАГМЕНТ полосы, а не JSON.

    Несущих утверждений два. Первое — `"<!DOCTYPE" not in response.text`:
    редирект, случайно доехавший до запроса htmx, придёт к тесту кодом 200 и
    телом целой страницы (`htmx_client` следует ему НЕЗАМЕТНО, как браузер), и
    отличить его от фрагмента можно только по отсутствию документа. Второе —
    скрытое поле с `form="ad-form"`: без него ключ никуда не уедет со следующей
    отправкой формы объявления, и человек потеряет только что загруженную
    картинку молча, увидев её на экране.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))],
    )

    assert response.status_code == 200, (
        f"запрос htmx получил {response.status_code} вместо фрагмента полосы — "
        "человек увидит общую плашку «Действие не выполнено» вместо плитки"
    )
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ: обработчик ответил перенаправлением, а "
        "клиент незаметно по нему прошёл — ровно то, чего не видит человек"
    )

    field = HIDDEN_KEY_FIELD.search(response.text)
    assert field is not None, (
        "во фрагменте нет скрытого поля ключа с form=\"ad-form\": загруженная "
        "картинка не доедет до объявления со следующим сохранением, и человек "
        "потеряет работу, видя плитку на экране"
    )

    key = field.group(1)
    assert IMAGE_KEY.fullmatch(key), (
        f"ключ {key!r} не той формы, которую примет правило владения при "
        "сохранении объявления — вложение не сохранится вовсе"
    )
    assert key.endswith(".png"), (
        f"расширение ключа {key!r} разошлось с сохранёнными байтами: PNG с "
        "альфой остаётся PNG, а имя, врущее о формате, воспроизводит issue #39"
    )
    assert f"thumbs/{key}" in response.text, (
        "плитка не спрашивает миниатюру: человек качает полноразмерный объект "
        "ради квадрата в 96 точек"
    )

    assert mock_s3.call_count == 2, (
        "сохранены не оба объекта: сжатая версия и миниатюра "
        f"(вызовов записи — {mock_s3.call_count})"
    )
    assert mock_s3.call_args_list[0].kwargs["key"] == key, (
        "в хранилище ушёл не тот ключ, что вернулся во фрагменте — плитка "
        "показывала бы объект, которого нет"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_without_htmx_redirects_to_the_editor(
    mock_s3, authed_client: AsyncClient
):
    """Без признака htmx тот же адрес отвечает 302 на редактор (FOUND-04).

    Половина пары, охраняющая путь деградации. Он заполнен ЧЕСТНО, а не
    заглушкой, хотя из интерфейса недостижим: у формы загрузки нет кнопки
    отправки (D-09), и прийти сюда без JavaScript можно только прямым POST.
    Адрес — `/ads/new`, потому что маршрут привязан к ПОЛЬЗОВАТЕЛЮ, а не к
    черновику (D-02), и адреса конкретного редактора он не знает.
    """
    response = await authed_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))],
        follow_redirects=False,
    )

    assert response.status_code == 302, (
        f"запрос без признака htmx получил {response.status_code} — путь "
        "деградации отвечает человеку без JavaScript фрагментом, который "
        "браузер покажет ему как целый документ"
    )
    assert response.headers["location"] == "/ads/new", (
        f"путь деградации ведёт на {response.headers.get('location')!r} вместо "
        "редактора — человек без JavaScript уезжает не туда, откуда пришёл"
    )


@pytest.mark.asyncio
async def test_upload_is_closed_by_the_router_access_gate(
    expired_client: AsyncClient, htmx_client: AsyncClient
):
    """Истёкший доступ закрывает загрузку ЗАВИСИМОСТЬЮ РОУТЕРА (критерий 3, D-01).

    Гейта в теле обработчика нет и быть не должно: `Depends(require_access)`
    висит на `ads_router` (`app/pages/__init__.py:143`), и маршрут, заведённый
    внутри него, получает отказ доступа не написав ни строки гейта.

    Отказ обязан быть ВИДЕН: 204 с заголовком перехода, а не молчание и не
    редирект. Редирект слой письма отрабатывает незаметно, и человек остался бы
    на прежнем экране, не узнав об отказе ни слова (FOUND-07). Подмены записи в
    хранилище здесь нет намеренно — до тела обработчика запрос не доходит вовсе,
    и патч скрыл бы ровно это свойство.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))],
    )

    assert response.status_code == 204, (
        f"загрузка при истёкшем доступе ответила {response.status_code} вместо "
        "204: гейт роутера её не закрыл, и человек без оплаченного доступа "
        "продолжает класть объекты в хранилище"
    )
    assert "HX-Location" in response.headers, (
        "в отказе нет заголовка перехода: человек остаётся на прежнем экране и "
        "не узнаёт, что доступ закрыт"
    )


# --- партия целиком: частичный успех, потолок, один код на три исхода ---------
#
# Критерий 2 фазы («успешно загруженные остаются прикреплёнными, даже если часть
# отвалилась») живёт ЗДЕСЬ. До этой группы правил партия проверялась ровно одним
# годным файлом, то есть случаем, в котором отваливаться нечему.


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_partial_batch_keeps_the_accepted_file(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Годный и негодный файл в ОДНОЙ партии: годный прикреплён, негодный назван.

    Это и есть запертый критерий 2, и проверяем мы здесь не «отказ работает», а
    то, что отказ ОДНОГО файла не уносит с собой РАБОТУ по другому. До перехода
    на один запрос свойство держалось само собой — файлы шли независимыми
    запросами; после перехода оно держится кодом и обязано быть утверждено.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png")),
            (UPLOAD_FIELD, ("sticker.webp", make_webp_bytes(), "image/webp")),
        ],
    )

    assert response.status_code == 200, (
        f"партия с одним негодным файлом получила {response.status_code}: "
        "человек увидит общую плашку вместо плитки и причины"
    )

    keys = HIDDEN_KEY_FIELD.findall(response.text)
    assert len(keys) == 1, (
        f"во фрагменте {len(keys)} скрытых полей ключа вместо одного: годный "
        f"файл партии не сохранён либо сохранён негодный — {keys}"
    )
    assert keys[0].endswith("_cat.png"), (
        f"прикреплён ключ {keys[0]!r}, а не годный файл партии"
    )

    rows = refusal_rows(response.text)
    assert len(rows) == 1, (
        f"строк отказа {len(rows)} вместо одной: {rows}. Отказ у каждого файла "
        "свой, и одна фраза на партию двух причин не сводит"
    )
    name, reason = rows[0]
    assert name == "sticker.webp", (
        f"строка отказа называет {name!r} — человек не поймёт, КАКОЙ из "
        "выбранных файлов не подошёл"
    )
    assert "JPEG" in reason and "PNG" in reason, (
        f"причина отказа {reason!r} не называет подходящие форматы: человек "
        "читает отказ как поломку сервиса"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_ceiling_takes_the_free_slots_and_refuses_the_rest(
    mock_s3,
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    owner: User,
    test_settings,
):
    """Потолок берёт ПЕРВЫЕ свободные места, партию целиком не отвергает (D-06).

    Это дословно сегодняшнее поведение: клиентская загрузка сверяла потолок
    перед КАЖДЫМ запросом, поэтому первые файлы уходили, а на остальные вставал
    отказ. Отвергнуть партию целиком было бы предсказуемее — и было бы сменой
    поведения плюс лишней работой человеку.
    """
    test_settings.max_images_per_ad = 4
    attached = [image_key(owner.id, f"old{index}.png") for index in range(2)]
    png = make_real_png_with_alpha_bytes()

    response = await htmx_client.post(
        "/ads/images",
        data={"images": attached},
        files=[
            (UPLOAD_FIELD, (f"{letter}.png", png, "image/png")) for letter in "abcde"
        ],
    )

    assert response.status_code == 200, (
        f"партия сверх потолка получила {response.status_code}: сервер отверг "
        "её целиком вместо того, чтобы взять свободные места"
    )

    keys = HIDDEN_KEY_FIELD.findall(response.text)
    assert keys[:2] == attached, (
        "уже прикреплённые ключи не переехали во фрагмент в прежнем порядке: "
        f"{keys[:2]} вместо {attached} — порядок ключей есть порядок отправки"
    )
    accepted_names = [key.split("_", 1)[-1] for key in keys[2:]]
    assert accepted_names == ["a.png", "b.png"], (
        f"на два свободных места приняты {accepted_names} вместо первых двух "
        "частей по порядку: человек получил не те файлы, что выбрал первыми"
    )

    rows = refusal_rows(response.text)
    assert [name for name, _ in rows] == ["c.png", "d.png", "e.png"], (
        f"строки отказа называют {[name for name, _ in rows]} вместо трёх "
        "лишних файлов: человек не узнает, какие именно не прикрепились"
    )
    for name, reason in rows:
        assert "4" in reason, (
            f"причина отказа {name!r} не называет числа мест ({reason!r}) — "
            "человек не знает, сколько вложений удалить"
        )

    assert mock_s3.call_count == 4, (
        "в хранилище ушло не два объекта с миниатюрами, а "
        f"{mock_s3.call_count} записей: лишние части партии всё-таки прочитаны "
        "и сохранены, то есть потолок считается ПОСЛЕ работы, а не до неё"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_own_keys_over_the_ceiling_are_not_erased_by_a_new_batch(
    mock_s3,
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    owner: User,
    test_settings,
):
    """Потолок управляет НОВЫМИ файлами и не трогает УЖЕ прикреплённые.

    ⚠️ ДОСТИЖИМОСТЬ БЕЗ НАПАДАЮЩЕГО, И НАЗВАНА ОНА ПОИМЁННО: `max_images_per_ad`,
    опущенный ниже числа вложений живого объявления. Одиннадцать СВОИХ
    синтаксически годных ключей при потолке десять — не подделка, а обычное
    состояние после смены настройки, и стирать его сервер права не имеет.

    Потолок при этом не ослаблен: свободных мест ноль, и каждая присланная
    часть получает свою строку про потолок, не доезжая до хранилища. Настоящей
    квотой остаётся отказ по длине на СОХРАНЕНИИ — там решается, что записать в
    базу, и отказать там обязательно.
    """
    test_settings.max_images_per_ad = 10
    attached = [image_key(owner.id, f"old{index}.png") for index in range(11)]

    response = await htmx_client.post(
        "/ads/images",
        data={"images": attached},
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))
        ],
    )

    assert response.status_code == 200, (
        f"партия при потолке ниже числа прикреплённых получила "
        f"{response.status_code}: подмены не будет, и человек не прочтёт причину"
    )

    keys = HIDDEN_KEY_FIELD.findall(response.text)
    assert len(keys) == 11, (
        f"во фрагменте {len(keys)} скрытых полей вместо одиннадцати: понижение "
        "настройки потолка отцепило от объявления вложения, которые человек "
        "прикрепил раньше и видит на экране"
    )
    assert keys == attached, (
        f"ключи переехали во фрагмент не в прежнем порядке: {keys} вместо "
        f"{attached} — порядок ключей есть порядок отправки"
    )

    rows = refusal_rows(response.text)
    assert [name for name, _ in rows] == ["cat.png"], (
        f"строки отказа называют {[name for name, _ in rows]} вместо одного "
        "присланного файла: человек не узнает, что именно не прикрепилось"
    )
    assert "10" in rows[0][1], (
        f"причина отказа {rows[0][1]!r} не называет числа мест — человек не "
        "знает, сколько вложений удалить"
    )

    assert mock_s3.call_count == 0, (
        f"в хранилище ушло {mock_s3.call_count} записей при нуле свободных мест: "
        "тело части прочитано ради результата, которому заведомо некуда деться"
    )
    assert EVENT_HEADER not in response.headers, (
        "ответ, не принявший ни одного файла, всё равно просит форму "
        "сохраниться: круг к серверу делается за работу, которой не было"
    )

    add_tile = response.text[response.text.index("media-tile--add") :].split(">", 1)[0]
    assert " hidden" in add_tile, (
        f"плитка «+ ФАЙЛ» ({add_tile!r}) осталась видимой при исчерпанном "
        "потолке: человек выберет файлы, которых сервер всё равно не примет"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_every_outcome_answers_two_hundred(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Отвергнуты ВСЕ файлы — ответ всё равно 200 с фрагментом (D-04).

    ⚠️ ЦЕНА ЭТОГО ПРАВИЛА НАЗВАНА, А НЕ СПРЯТАНА: здесь 200 говорит неправду,
    изменения не было. Плата принята сознательно в обмен на то, что человек
    читает ПРИЧИНУ: на любом коде, кроме 422, слой письма подмены не делает
    вовсе, и точный текст про форматы уступил бы место общей плашке.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[
            (UPLOAD_FIELD, ("one.webp", make_webp_bytes(), "image/webp")),
            (UPLOAD_FIELD, ("two.webp", make_webp_bytes(), "image/webp")),
        ],
    )

    assert response.status_code == 200, (
        f"партия, отвергнутая целиком, получила {response.status_code}: подмены "
        "не будет, и человек прочтёт «Действие не выполнено» вместо причины"
    )
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ вместо фрагмента полосы"
    )
    assert HIDDEN_KEY_FIELD.search(response.text) is None, (
        "во фрагменте есть скрытое поле ключа, хотя не принят ни один файл"
    )
    assert len(refusal_rows(response.text)) == 2, (
        f"строк отказа {len(refusal_rows(response.text))} вместо двух: причина "
        "названа не каждому отвергнутому файлу"
    )
    assert "Действие не выполнено" not in response.text, (
        "во фрагменте общая плашка аварии — ровно то, что D-04 убирает с экрана"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_a_foreign_key_is_not_echoed_back(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient, owner: User
):
    """Чужой ключ из включения полосы во фрагмент НЕ переиздаётся (D-07, T-12-12).

    Без этой сверки сервер начал бы печатать в разметку ключи, за которые
    сегодня отвечает только браузер: список текущих ключей приходит из
    документа, а документ клиент вправе подделать.

    ⚠️ ВТОРОЕ УТВЕРЖДЕНИЕ НЕ МЕНЕЕ ВАЖНО: файловые части при подделанном ключе
    не обрабатываются ВОВСЕ. Работа, сделанная ради запроса, уже признанного
    подделанным, оставила бы в хранилище объекты-сироты.
    """
    foreign = image_key(owner.id + 1, "stolen.png")

    response = await htmx_client.post(
        "/ads/images",
        data={"images": [foreign]},
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))
        ],
    )

    assert response.status_code == 200, (
        f"подделанный ключ получил {response.status_code} вместо фрагмента: "
        "подмены не будет, и человек не прочтёт, что случилось"
    )
    assert foreign not in response.text, (
        "чужой ключ вернулся во фрагменте: сервер переиздал в разметку то, "
        "владения чем никто не подтверждал"
    )
    assert HIDDEN_KEY_FIELD.search(response.text) is None, (
        "во фрагменте осталось скрытое поле ключа — подделанный список ключей "
        "частично пережил сверку"
    )

    rows = refusal_rows(response.text)
    assert len(rows) == 1, (
        f"строк отказа {len(rows)} вместо одной: {rows}"
    )
    assert "недоступно" in rows[0][1], (
        f"причина отказа {rows[0][1]!r} не говорит о недоступном вложении"
    )

    assert mock_s3.call_count == 0, (
        f"в хранилище ушло {mock_s3.call_count} записей при подделанном ключе: "
        "файловые части прочитаны и сохранены, то есть появились сироты"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_an_own_key_survives_a_foreign_key_in_the_same_batch(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient, owner: User
):
    """Смешанная партия: СВОЙ ключ остаётся, чужой отвергнут (гап 1, CR-02).

    Сосед правила выше, а не его переписывание. То правило утверждает, что
    чужое значение во фрагмент не переиздаётся; здесь утверждается вторая
    половина того же свойства — что отказ чужому не уносит с экрана СВОЁ.

    Почему это потеря РАБОТЫ, а не косметика: полоса вложений после плана 12-03
    есть ЕДИНСТВЕННЫЙ источник списка ключей в документе, и подмена её
    содержимого выносит все скрытые поля. Пустая полоса в ответе означает, что
    следующее автосохранение — одно нажатие клавиши — запишет объявление БЕЗ
    вложений.
    """
    mine = image_key(owner.id, "mine.png")
    foreign = image_key(owner.id + 1, "stolen.png")

    response = await htmx_client.post(
        "/ads/images",
        data={"images": [mine, foreign]},
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))
        ],
    )

    assert response.status_code == 200, (
        f"смешанная партия получила {response.status_code} вместо фрагмента: "
        "подмены не будет, и человек не прочтёт, что случилось"
    )

    keys = HIDDEN_KEY_FIELD.findall(response.text)
    assert keys == [mine], (
        f"во фрагменте скрытые поля {keys} вместо [{mine!r}]: законное вложение "
        "отцеплено заодно с подделанным, и следующее сохранение запишет "
        "объявление без него"
    )
    assert foreign not in response.text, (
        "чужой ключ вернулся во фрагменте: сервер переиздал в разметку то, "
        "владения чем никто не подтверждал"
    )

    rows = refusal_rows(response.text)
    assert len(rows) == 1, (
        f"строк отказа {len(rows)} вместо одной: {rows}"
    )
    assert "недоступно" in rows[0][1], (
        f"причина отказа {rows[0][1]!r} не говорит о недоступном вложении"
    )

    assert mock_s3.call_count == 0, (
        f"в хранилище ушло {mock_s3.call_count} записей при подделанном ключе в "
        "партии: работа ради запроса, признанного подделанным, всё-таки сделана"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_the_keys_that_survive_a_refusal_are_the_ones_the_next_save_persists(
    mock_s3,
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    owner: User,
    db_session: AsyncSession,
):
    """Правило на ДВА обработчика: что пережило отказ, то и доезжает до базы.

    ⚠️ ТАКОГО ПРАВИЛА В СУИТЕ НЕ БЫЛО НИ ОДНОГО, И ИМЕННО ПОЭТОМУ ДЕФЕКТ ПРОШЁЛ
    ЗЕЛЁНЫМ. Порознь оба обработчика безупречны: загрузка отвечает 200 с
    фрагментом, сохранение честно пишет то, что пришло формой. Теряется работа
    человека РОВНО НА СТЫКЕ — фрагмент приходит без скрытых полей, форма
    объявления сериализует ноль вложений, и `ad.images` становится пустым.

    Поэтому ключи не подставляются в запрос сохранения «правильными», а
    ВЫНИМАЮТСЯ из ответа загрузки: тест обязан отправить то, что отправит
    браузер, а не то, что приложение считает правильным.
    """
    mine = image_key(owner.id, "mine.png")
    foreign = image_key(owner.id + 1, "stolen.png")
    # Идентификатор снимается ДО истечения сессии: после `expire_all` обращение
    # к полю посеянного объекта уехало бы ленивой подгрузкой в синхронном
    # контексте и уронило бы тест отказом драйвера вместо утверждения.
    ad_id = (await _seed_ad(db_session, owner.id, images=[mine])).id

    upload = await htmx_client.post(
        "/ads/images",
        data={"images": [mine, foreign]},
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))
        ],
    )
    assert upload.status_code == 200, (
        f"загрузка ответила {upload.status_code} вместо фрагмента полосы"
    )

    survived = HIDDEN_KEY_FIELD.findall(upload.text)

    saved = await htmx_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(images=survived),
        headers=HX_HEADERS,
    )
    assert saved.status_code == 200, (
        f"сохранение объявления ответило {saved.status_code}: скрытые поля, "
        "пережившие отказ, не приняты сверкой владения на сохранении"
    )

    db_session.expire_all()
    stored = (
        await db_session.execute(select(Ad).where(Ad.id == ad_id))
    ).scalar_one()
    assert stored.images == [mine], (
        f"в базе осталось {stored.images} вместо [{mine!r}]: одно автосохранение "
        "после неудачной попытки загрузки стёрло вложение, которое человек "
        "прикрепил раньше и видел на экране"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_a_refusal_row_survives_the_autosave_the_same_response_triggers(
    mock_s3,
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    owner: User,
    db_session: AsyncSession,
):
    """Гап 2: строка отказа обязана пережить круг, который ЭТОТ ЖЕ ответ и заказывает.

    ⚠️ КРУГ ЗАМКНУТ САМИМ ОТВЕТОМ ЗАГРУЗКИ, И ПОТОМУ ЭТО НЕ РЕДКИЙ СЛУЧАЙ, А
    САМЫЙ ЧАСТЫЙ ПУТЬ. Ответ смешанной партии несёт
    ``HX-Trigger-After-Swap: ads-image-attached``; форма объявления слушает это
    событие ``from:body`` и немедленно уходит автосохранением — ровно тем
    запросом, который здесь и подаётся вторым. Если ответ автосохранения принесёт
    внеполосный ``#media-tray``, подмена заменит узел ЦЕЛИКОМ и сотрёт строку
    отказа, за которую D-04 заплатил лживым кодом 200: человек не успеет
    прочитать, КАКОЙ его файл не подошёл и почему. Выбранный им файл исчезнет
    МОЛЧА — ровно тот запрет, который фаза держит.

    Правило рендерит ДВА ФРАГМЕНТА ДРУГ ПРОТИВ ДРУГА: ответ загрузки
    разбирается на строки отказа и скрытые поля, и ровно эти ключи уходят
    следующим запросом в редактор. Порознь оба обработчика зелены — дефект
    живёт на стыке, и правил на стык в суите до Фазы 12 не было ни одного.
    """
    # Идентификатор снимается ДО истечения сессии: после `expire_all` обращение
    # к полю посеянного объекта уехало бы ленивой подгрузкой в синхронном
    # контексте и уронило бы тест отказом драйвера вместо утверждения.
    ad_id = (await _seed_ad(db_session, owner.id)).id

    upload = await htmx_client.post(
        "/ads/images",
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png")),
            (UPLOAD_FIELD, ("sticker.webp", make_webp_bytes(), "image/webp")),
        ],
    )
    assert upload.status_code == 200, (
        f"загрузка ответила {upload.status_code} вместо фрагмента полосы"
    )

    rows = refusal_rows(upload.text)
    assert len(rows) == 1, (
        f"строк отказа в ответе загрузки {len(rows)} вместо одной: {rows} — "
        "дальше нечему переживать круг, и правило измеряло бы пустоту"
    )
    attached = HIDDEN_KEY_FIELD.findall(upload.text)
    assert len(attached) == 1, (
        f"годный файл партии не прикреплён: скрытых полей {len(attached)} — "
        f"{attached}"
    )

    # Тот самый запрос, который поднимает слушатель `ads-image-attached`:
    # скрытые поля берутся ИЗ ОТВЕТА, а `remove_image` не подаётся — состав
    # вложений этим запросом не меняется.
    saved = await htmx_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(images=attached),
        headers=HX_HEADERS,
    )
    assert saved.status_code == 200, (
        f"автосохранение ответило {saved.status_code}: ключ, только что выданный "
        "загрузкой, не принят сверкой владения на сохранении"
    )
    assert 'id="media-tray"' not in saved.text, (
        "ответ автосохранения принёс узел полосы: внеполосная подмена заменит "
        "её целиком и унесёт с экрана строку отказа, которую человек не успел "
        "прочитать — выбранный им файл пропадёт МОЛЧА"
    )

    db_session.expire_all()
    stored = (
        await db_session.execute(select(Ad).where(Ad.id == ad_id))
    ).scalar_one()
    assert stored.images == attached, (
        f"в базе {stored.images} вместо {attached}: ключ принятого файла не "
        "доехал до записи объявления"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_a_rejected_name_is_normalised_before_it_is_shown(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Имя ОТВЕРГНУТОГО файла нормализуется ДО показа (D-05, T-12-14).

    Имя на плитке нормализацию проходило всегда — оно берётся из сохранённого
    ключа. Имя отвергнутого файла не проходило её НИКОГДА: это сырой ввод
    отправителя, и до этой фазы оно на экран не попадало вовсе. Одного
    автоэкранирования шаблонизатора мало — оно закрывает разметку, но не
    закрывает имя длиной в четыре тысячи символов.
    """
    hostile = (
        "../../подполье <script>alert(1)</script>" + "x" * 4000 + ".webp"
    )

    response = await htmx_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, (hostile, make_webp_bytes(), "image/webp"))],
    )

    assert response.status_code == 200
    rows = refusal_rows(response.text)
    assert len(rows) == 1, f"строк отказа {len(rows)} вместо одной: {rows}"

    shown = rows[0][0]
    assert "../" not in response.text, (
        "сегменты пути из клиентского имени доехали до разметки"
    )
    assert "<script>" not in response.text, (
        "разметка из клиентского имени доехала до документа человека"
    )
    assert re.fullmatch(r"[A-Za-z0-9._-]+", shown), (
        f"показанное имя {shown!r} вышло за безопасный набор символов"
    )
    assert len(shown) <= 100, (
        f"показанное имя длиной {len(shown)}: строка отказа растягивает полосу "
        "и выталкивает плитки с экрана"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_oversized_beats_unsupported(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient, test_settings
):
    """Отказ ПО РАЗМЕРУ стоит выше распознавания типа — порядок перенесён дословно.

    Свойство наблюдаемо: тело, которое ОДНОВРЕМЕННО превышает предел и не
    является изображением, получает отказ по размеру. Порядок не вкусовой, а
    вынужденный потоковым чтением, и перестановка сделала бы вход мягче ровно на
    тот класс запросов, ради которого предел введён.
    """
    test_settings.max_image_size_mb = 1
    junk = b"\x00" * (1024 * 1024 + 1024)

    response = await htmx_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, ("huge.bin", junk, "application/octet-stream"))],
    )

    assert response.status_code == 200
    rows = refusal_rows(response.text)
    assert len(rows) == 1, f"строк отказа {len(rows)} вместо одной: {rows}"

    name, reason = rows[0]
    assert name == "huge.bin", f"строка отказа называет {name!r}"
    assert "size exceeds" in reason, (
        f"причина отказа {reason!r} не про размер: порядок проверок переставлен, "
        "и тело произвольного размера читается целиком ради распознавания типа"
    )
    assert "JPEG" not in reason, (
        f"причина отказа {reason!r} про форматы, а не про размер"
    )


# --- переехавшие утверждения о входе: отказ и авария хранилища ----------------
#
# Оба правила ниже приехали из суиты снятого JSON-входа (план 12-05, G-8) и
# приехали по-разному, потому что форма ответа сменилась не у обоих.
#
# ⚠️ ПЕРВОЕ ПЕРЕЕХАЛО ПЕРЕВЁРНУТЫМ: прежде оно ждало кода отказа и поля причины
# в теле JSON, теперь ждёт кода 200 и строки отказа во фрагменте (D-04). Отказ
# САМОГО приёма — то, что содержимое в хранилище не уходит, — утверждается в
# суите сервиса; здесь утверждается то, что человек об этом УЗНАЁТ.
#
# ⚠️ ВТОРОЕ ПЕРЕЕХАЛО КАК ЕСТЬ, И ЭТО НЕ НЕДОСМОТР: авария хранилища формы ответа
# не сменила и сменить не должна.


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_an_svg_named_as_png_is_refused_in_the_fragment(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """CR-02: SVG под именем PNG отвергается, и человек читает ПОЧЕМУ.

    Прежде это правило ждало кода 400 и поля `detail`. С D-04 таких ответов на
    этом пути нет вовсе: на любом коде, кроме 422, рантайм разметки подмены не
    делает, и точный текст про JPEG/PNG уступил бы место общей плашке. Поэтому
    утверждение перевёрнуто, а не снято: 200 с фрагментом и СВОЯ строка отказа.

    `call_count == 0` обязателен ровно по прежнему основанию: одна строка отказа
    доказывает мало — её же даёт и превышение размера, — а смысл правила в том,
    что исполняемый документ в хранилище не попадает вовсе и браузеру с origin
    хранилища не отдаётся.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, ("logo.png", SVG_BYTES, "image/png"))],
    )

    assert response.status_code == 200, (
        f"SVG под именем PNG получил {response.status_code}: подмены не будет, и "
        "человек прочтёт «Действие не выполнено» вместо причины"
    )
    assert HIDDEN_KEY_FIELD.search(response.text) is None, (
        "во фрагменте есть скрытое поле ключа: исполняемый документ прикреплён "
        "к объявлению"
    )

    rows = refusal_rows(response.text)
    assert len(rows) == 1, f"строк отказа {len(rows)} вместо одной: {rows}"
    name, reason = rows[0]
    assert name == "logo.png", (
        f"строка отказа называет {name!r} — человек не поймёт, какой файл не подошёл"
    )
    assert "JPEG" in reason, (
        f"причина отказа {reason!r} не называет подходящие форматы"
    )
    assert "<script>" not in response.text, (
        "содержимое отвергнутого документа доехало до разметки человека"
    )

    assert mock_s3.call_count == 0, (
        f"в хранилище ушло {mock_s3.call_count} записей: SVG принят, и отданный "
        "браузеру с origin хранилища он исполнит свой скрипт в его контексте"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_a_storage_failure_still_answers_bad_gateway(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Авария хранилища отвечает 502, а НЕ фрагментом с 200.

    ⚠️ ГРАНИЦА «ВСЕГДА 200» ПРОХОДИТ ЗДЕСЬ, И ПРОХОДИТ ОНА НАМЕРЕННО. D-04
    требует 200 для отказа ФАЙЛУ — человеку есть что сказать о его файле. Провал
    записи объекта есть отказ ИНФРАСТРУКТУРЫ: сказать «ваш файл не подошёл»
    значило бы соврать, а показать плитку — соврать дважды, потому что объекта в
    хранилище нет. Общая плашка «Действие не выполнено... через минуту» здесь
    как раз правдива, и путь до неё — код ответа, отличный от 200.

    `call_count == 1` держит парное свойство сервиса: послабление, данное
    МИНИАТЮРЕ (её провал загрузку не проваливает, P-7), на сжатую версию не
    расползлось — второй записи после аварии первой не делается.
    """
    mock_s3.side_effect = RuntimeError("bucket is down")

    response = await htmx_client.post(
        "/ads/images",
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))
        ],
    )

    assert response.status_code == 502, (
        f"авария хранилища ответила {response.status_code}: человек увидел бы "
        "плитку картинки, которой в хранилище нет, и потерял бы её при "
        "следующей загрузке страницы"
    )
    assert mock_s3.call_count == 1, (
        f"обращений к хранилищу {mock_s3.call_count} вместо одного: миниатюра "
        "пишется после провала сжатой версии, то есть послабление P-7 "
        "расползлось на оба объекта"
    )


# --- черновик после удачной загрузки -----------------------------------------
#
# Сегодня черновик на `/ads/new` создаёт ПЕРВАЯ загруженная картинка: клиентский
# обработчик загрузки после успеха поднимал событие на форме объявления. Со
# снятием этого кода вызов исчезает, и человек, прикрепивший картинку и не
# набравший ни символа, терял бы её при обновлении страницы. Всплытие события
# формы ЗАГРУЗКИ до формы объявления не долетает — они СОСЕДИ, а не родитель и
# потомок, — поэтому связь восстанавливается заголовком ответа и слушателем.


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_a_successful_upload_asks_the_ad_form_to_save(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Удачная загрузка просит форму объявления сохраниться — заголовком ответа.

    ⚠️ ЗАГОЛОВОК ИМЕННО «ПОСЛЕ ПОДМЕНЫ», И РАЗНИЦА НАБЛЮДАЕМА. Обычный
    заголовок события поднимает его ДО подмены — форма объявления
    сериализовалась бы в момент, когда новых скрытых полей в документе ещё нет,
    и первое же автосохранение сохранило бы объявление БЕЗ только что
    загруженной картинки. Ровно та потеря работы, ради предотвращения которой
    механизм и заводится.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[
            (UPLOAD_FIELD, ("cat.png", make_real_png_with_alpha_bytes(), "image/png"))
        ],
    )

    assert response.status_code == 200
    assert response.headers.get(EVENT_HEADER) == UPLOAD_EVENT, (
        f"ответ удачной загрузки несёт {response.headers.get(EVENT_HEADER)!r} "
        f"вместо {UPLOAD_EVENT!r} в заголовке события после подмены: человек, "
        "прикрепивший картинку на /ads/new и не набравший ни символа, потеряет "
        "её при обновлении страницы — черновика не создастся"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_a_fully_refused_upload_asks_for_nothing(
    mock_s3, authed_client: AsyncClient, htmx_client: AsyncClient
):
    """Принято НОЛЬ файлов — заголовка события в ответе нет.

    Сохранять нечего: состояние вложений не изменилось. Лишний круг к серверу
    стоил бы человеку и ожидания, и записи в журнал — за работу, которой не
    было.
    """
    response = await htmx_client.post(
        "/ads/images",
        files=[(UPLOAD_FIELD, ("sticker.webp", make_webp_bytes(), "image/webp"))],
    )

    assert response.status_code == 200
    assert EVENT_HEADER not in response.headers, (
        "ответ, не принявший ни одного файла, всё равно просит форму "
        "сохраниться: круг к серверу делается за работу, которой не было"
    )


@pytest.mark.asyncio
async def test_the_ad_form_listens_for_the_upload_event(authed_client: AsyncClient):
    """Форма объявления слушает событие загрузки ОТ ТЕЛА ДОКУМЕНТА.

    ⚠️ «ОТ ТЕЛА ДОКУМЕНТА» — НЕ УКРАШЕНИЕ, А ЕДИНСТВЕННЫЙ РАБОТАЮЩИЙ АДРЕС.
    Событие поднимается на узле, ПОСЛАВШЕМ запрос, — на форме загрузки, — и
    всплывает по дереву документа. Форма загрузки форме объявления СОСЕД, а не
    потомок, поэтому обычное всплытие до неё не долетает.

    Прочие условия отправки и очередь наложения проверяются здесь же: перевод
    списка условий на новую строку легко уносит соседнее условие молча.
    """
    page = await authed_client.get("/ads/new")

    assert page.status_code == 200
    trigger = _attr_value(page.text, 'id="ad-form"', "hx-trigger")

    assert f"{UPLOAD_EVENT} from:body" in trigger, (
        f"перечень условий отправки формы объявления — {trigger!r}: события "
        "загрузки в нём нет, и удачная загрузка черновика не создаст"
    )
    for kept in ("submit", "keyup changed delay:2s", "change delay:2s"):
        assert kept in trigger, (
            f"условие {kept!r} исчезло из перечня {trigger!r}: вместе с ним "
            "исчезает автосохранение, ради которого форма и написана"
        )
