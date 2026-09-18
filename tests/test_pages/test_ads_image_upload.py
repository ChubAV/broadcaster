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

import pytest
from httpx import AsyncClient
from PIL import Image

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


# --- построители настоящих изображений ---------------------------------------
#
# Скопированы из `tests/test_routes/test_uploads.py:103-151` намеренно, а не
# ввезены оттуда: тестовый модуль не библиотека, и импорт одного из другого
# связал бы два файла порядком сборки и превратил бы вспомогательную функцию в
# неявный публичный контракт (тот же довод записан в самом источнике).
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
