"""Рендер-тесты редактора объявления — точка опоры ADS-04 и ADS-06 (D-21).

До этого файла `/ads/new` и `/ads/{id}/edit` не рендерились НИ ОДНИМ тестом
суиты: шаблонные глобалы изображений в `app/pages/common.py` вызывали
`get_settings()` в обход подмены зависимостей, поэтому страница рендерилась
только при наличии `.env` рядом с процессом. Планы 02-04 и 02-05 переделывают
именно этот экран — без рендер-теста их правки нечем удержать (T-02-03).

Эталон формы взят из `tests/test_pages/test_responsive_markup.py`: посев через
`db_session`, запрос через `authed_client`, утверждения на РЕАЛЬНЫХ строках
данных. Утверждения на один только код ответа тут бесполезны: потеря контекста
макроса даёт 200 с пустой страницей.
"""

import re
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.ad import Ad
from app.models.user import User
from app.pages.ads import CAPTION_LIMIT, TEXT_LIMIT, TEXT_WARN_RATIO
from app.pages.common import _thumb_image_url
# ⚠️ ЭТО ИМЯ ВВОЗИТСЯ, А НЕ ПОВТОРЯЕТСЯ ОБРАЗЦОМ, И РАЗНИЦА НЕСУЩАЯ (Фаза 12,
# план 12-11). Идентификатор плитки в документе и идентификатор, который
# называет блок СНЯТИЯ ответа убирания, обязаны совпадать — и совпадать не по
# счастью, а потому, что их производит ОДНА функция. Собери правило значение
# заново (хеш, срез, приставка), и оно мерило бы собственную формулировку:
# разойдись два написания — правило осталось бы зелёным, а плитка перестала бы
# сниматься с экрана. Ввоз привязывает утверждение к ПРАВИЛУ ПРОИЗВОДСТВА, а не
# к его сегодняшнему выводу.
from app.services.image_keys import media_dom_id
# ⚠️ ИМПОРТА ТЕКСТА ОТКАЗА ЗДЕСЬ БОЛЬШЕ НЕТ (Фаза 12, план 12-03). Имя
# `UNSUPPORTED_IMAGE_MESSAGE` ввозилось из снимаемого модуля маршрутов загрузки,
# и держал его ЕДИНСТВЕННЫЙ читатель — утверждение о присутствии ВТОРОЙ копии
# текста в отрендеренном редакторе. Сама не-транспортная половина загрузки
# переехала в `app/services/image_upload.py` планом 12-01, то есть имя не
# исчезло, а сменило дом; вторая же копия снята вместе с ручной загрузкой,
# читателей у имени в этом модуле не осталось, и оставленный импорт утверждал
# бы связь, которой нет. Гарантия «человек читает точную причину» переехала на
# тест фрагмента полосы.

# Форма ключа вложения — источник правды `app/services/image_upload.py`
# (переезд плана 12-01; прежде правду держал модуль маршрутов загрузки):
# `{user_id}/{32 hex}_{имя}`. Свой ключ строится тем же способом, что в
# tests/test_pages/test_ads_image_ownership.py: значение обязано пройти
# `own_image_keys` из плана 02-02, иначе тест меряет отказ, а не поведение.
FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
HX_HEADERS = {**FORM_HEADERS, "HX-Request": "true"}


def image_key(user_id: int, name: str = "photo.jpg") -> str:
    return f"{user_id}/{uuid4().hex}_{name}"


def form_body(
    title: str = "Заголовок",
    text: str = "Текст",
    images: list[str] | None = None,
    extra: list[tuple[str, str]] | None = None,
) -> str:
    fields: list[tuple[str, str]] = [("title", title), ("text", text)]
    fields += [("images", value) for value in images or []]
    fields += extra or []
    return urlencode(fields)


async def _ads_count(db: AsyncSession, user_id: int) -> int:
    return int(
        await db.scalar(select(func.count()).select_from(Ad).where(Ad.user_id == user_id))
        or 0
    )


async def _only_ad(db: AsyncSession, user_id: int) -> Ad:
    db.expire_all()
    return (
        await db.execute(select(Ad).where(Ad.user_id == user_id))
    ).scalars().one()


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _stranger(db: AsyncSession) -> User:
    """Второй пользователь — владелец «чужого» объявления.

    Форма посева взята из tests/test_pages/test_schedule_ownership.py: чужая
    запись обязана принадлежать НАСТОЯЩЕМУ пользователю, иначе отказ мог бы
    объясняться отсутствием владельца, а не проверкой владения.
    """
    user = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _attr_value(html: str, anchor: str, attr: str) -> str:
    """Значение атрибута элемента, опознанного по подстроке `anchor`.

    Разбор строкой — тот же приём, что уже применяют этот файл и
    tests/test_pages/test_responsive_markup.py: новой зависимости разбора HTML
    ради одного скрытого поля не заводится. Отсутствие элемента или атрибута
    поднимает ValueError — то есть тест падает, а не молча меряет пустоту.
    """
    start = html.index(anchor)
    opened = html.index(f'{attr}="', start) + len(attr) + 2
    return html[opened : html.index('"', opened)]


# --- разбор ответа убирания (Фаза 12, план 12-11) ----------------------------
#
# ⚠️ ДВА УТВЕРЖДЕНИЯ О ПОЛЯХ ВЛОЖЕНИЙ ЧИТАЮТСЯ ДВУМЯ РАЗНЫМИ ИНСТРУМЕНТАМИ, И
# ПУТАТЬ ИХ НЕЛЬЗЯ: на этом стои́т весь довод о том, что правило стало СИЛЬНЕЕ.
#   (1) НУЛЕВОЙ СЧЁТ снимается над ИМЕНЕМ поля — над вхождением `name="images"`,
#       и ни над чем более узким. Ни порядок атрибутов, ни наличие
#       `type="hidden"`, `value=…` или `form="ad-form"` в это утверждение не
#       входят: заявлено, что поля вложений в ответе НЕТ НИ ОДНОГО ни в каком
#       написании. Снятый образцом полного набора атрибутов, этот счёт был бы
#       зелен от поля, написанного в другом порядке атрибутов, — то есть заявлял
#       бы «полей нет», не умея их увидеть.
#   (2) ЗНАЧЕНИЯ достаёт образец ниже — полным набором атрибутов, потому что ему
#       нужно ДОСТАТЬ значение, а не пересчитать поля. Образец свой, в этом
#       модуле: перекрёстных ввозов помощников между модулями тестов здесь нет.
HIDDEN_KEY_FIELD = re.compile(
    r'<input type="hidden" name="images" value="([^"]+)" form="ad-form">'
)

# Любой тег ответа — для разбора внеполосных блоков по способу подмены.
_ANY_TAG = re.compile(r"<[^<>]+>")
_TAG_ID = re.compile(r'\bid="([^"]+)"')
_TAG_NAME = re.compile(r'\bname="([^"]+)"')

# --- вычитающая метка убирания (Фаза 12, план 12-12) -------------------------
#
# ⚠️ ИМЯ ПОЛЯ МЕТКИ НАЗВАНО ЗДЕСЬ ЛИТЕРАЛОМ, А НЕ ВВЕЗЕНО ИЗ ПРИЛОЖЕНИЯ, И
# ОСНОВАНИЕ ТО ЖЕ, ЧТО У ИМЕНИ ПОЛЯ ВЛОЖЕНИЙ ВЫШЕ: это КОНТРАКТ МЕЖДУ
# ДОКУМЕНТОМ И ОБРАБОТЧИКОМ СОХРАНЕНИЯ. Ответ убирания печатает поле с этим
# именем, документ увозит его следующей отправкой формы, обработчик читает его
# по тому же имени. Ввезённая константа утверждала бы имя саму о себе и зеленела
# бы ровно тогда, когда переименование разорвало бы связь ответа с разбором.
#
# ⚠️ ИМЯ НЕ РАВНО `images`, И ЭТО НЕСУЩЕЕ СВОЙСТВО, А НЕ ВКУС. Поле метки только
# ВЫЧИТАЕТ; будь оно названо именем поля вложений, тот же самый ответ открыл бы
# путь ВВОДА ключа в состав вложений — и открыл бы его по НАПИСАНИЮ, без единой
# правки обработчика (T-12-12-02).
REMOVAL_MARK_FIELD_NAME = "removed_images"
REMOVAL_MARK_FIELD = re.compile(
    r'<input type="hidden" name="removed_images" value="([^"]+)">'
)
# Тег поля метки целиком — для вычитания меток из ответа перед утверждением о
# том, что ВНЕ них убранного ключа в ответе не осталось. Порядок атрибутов
# образцу безразличен: он опознаёт тег по ИМЕНИ поля, а не по полному набору.
_MARK_FIELD_TAG = re.compile(r'<input[^<>]*name="removed_images"[^<>]*>')


def removal_marks(html: str) -> list[str]:
    """Значения вычитающих меток ответа — в порядке появления.

    ⚠️ ЗНАЧЕНИЕ БЕРЁТСЯ ИЗ ОТВЕТА СЕРВЕРА, А НЕ ПОДСТАВЛЯЕТСЯ ТЕСТОМ, И РАЗНИЦА
    НЕСУЩАЯ (Фаза 12, план 12-12, D-19). Метка — это то, что документ увезёт
    СЛЕДУЮЩЕЙ отправкой формы; подставив её от себя, правило мерило бы
    собственную формулировку, а не механизм, и осталось бы зелёным ровно тогда,
    когда ответ перестал бы метку печатать.
    """
    return REMOVAL_MARK_FIELD.findall(html)


def removed_dom_ids(html: str) -> list[str]:
    """Идентификаторы, названные ответом к СНЯТИЮ, в порядке появления.

    ⚠️ ОБРАЗЕЦ ПРИШПИЛЕН К СПОСОБУ ПОДМЕНЫ `delete`, И ЭТО НЕСУЩЕЕ ТРЕБОВАНИЕ,
    А НЕ АККУРАТНОСТЬ. Перечень, собранный с ЛЮБОГО внеполосного блока ответа,
    краснел бы на ЗАКОННОЙ работе соседей: тем же ответом приезжают плитка
    добавления (`media-add-tile`, задача 2 этого плана) и вычитающая метка
    убирания (`media-tombstones`, план 12-12) — оба ровно тогда же, когда блоки
    снятия, потому что условие у них одно: состав вложений изменён ЭТИМ
    запросом. Попав в перечень, они сделали бы равенство ложным, не тронув
    предмета правила ни на символ.

    Поэтому перечень измеряет «кого этот ответ УНОСИТ», а не «сколько блоков он
    вообще несёт». Ровно это и есть предмет: ВЛАСТЬ ОТВЕТА НАД ЧУЖИМ
    СОСТОЯНИЕМ. Следующему читателю: не «чинить» образец, расширив его до всех
    внеполосных блоков.

    Разбор строкой — тот же приём, что применяют соседние помощники модуля:
    новой зависимости разбора HTML ради одного атрибута не заводится. Порядок
    атрибутов внутри тега образцу безразличен.
    """
    found: list[str] = []
    for tag in _ANY_TAG.findall(html):
        if 'hx-swap-oob="delete"' not in tag:
            continue
        match = _TAG_ID.search(tag)
        found.append(match.group(1) if match else "")
    return found


def _counter_class(html: str) -> str:
    """Значение `class` у счётчика длины — и только у него.

    Утверждать наличие подстроки `counter--warn` во всей странице бесполезно:
    те же имена классов встречаются в узловой сборке счётчика, которая живёт в
    том же файле шаблона. Такая проверка зелена при ЛЮБОМ пороге и меряет
    наличие скрипта, а не выбор порога.

    Атрибут стоит ПЕРЕД `id`, поэтому элемент отыскивается назад от якоря.
    Отсутствие элемента или атрибута поднимает ValueError — тест падает, а не
    молча меряет пустоту.
    """
    anchor = html.index('id="text-counter"')
    element = html[html.rindex("<span", 0, anchor) : anchor]
    opened = element.index('class="') + len('class="')
    return element[opened : element.index('"', opened)]


def _ad_id_from(html: str) -> str:
    """Идентификатор объявления, который СЕРВЕР вернул в ответе автосохранения.

    Значение приезжает внеполосно скрытым полем `#ad-id-field` и подменяет то
    же поле внутри никогда не перерисовываемой формы. Тест обязан брать
    следующий адрес и следующий идентификатор ИЗ ОТВЕТА, а не назначать их
    рукой: назначенный рукой идентификатор проверяет замысел теста, а не
    контракт, который получает браузер (02-REVIEW.md, IN-06).
    """
    return _attr_value(html, 'id="ad-id-field"', "value")


async def _seed_ad(
    db: AsyncSession,
    title: str = "Осенний завоз",
    images: list[str] | None = None,
    user_id: int | None = None,
) -> Ad:
    if user_id is None:
        user_id = (await _user(db)).id
    ad = Ad(
        user_id=user_id,
        title=title,
        text="Полный текст объявления про осенний завоз",
        images=images or [],
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


# --- ADS-04: экран создания рендерится --------------------------------------


@pytest.mark.asyncio
async def test_ads_new_renders(authed_client: AsyncClient):
    """`GET /ads/new` отдаёт 200 и форму с полями названия и текста (D-21)."""
    response = await authed_client.get("/ads/new")

    assert response.status_code == 200
    html = response.text
    assert 'name="title"' in html
    assert 'name="text"' in html
    # Форма создания уходит на свой маршрут, а не на редактирование.
    assert 'action="/ads/new"' in html


@pytest.mark.asyncio
async def test_editor_file_picker_offers_only_sendable_formats(
    authed_client: AsyncClient,
):
    """Диалог файлов сужен до форматов, которые принимают все три мессенджера.

    Issue #39. ``accept`` обходится выбором «все файлы» и перетаскиванием — это
    подсказка диалогу, а не проверка (T-Q39-02). Он удешевляет типовой отказ, но
    авторитетом остаётся серверное распознавание по содержимому.

    ⚠️ ВТОРАЯ ПОЛОВИНА ПРАВИЛА СНЯТА ВМЕСТЕ СО ВТОРОЙ КОПИЕЙ ТЕКСТА (D-12 Фазы
    12, план 12-03), И ПРЕЖНЯЯ РЕДАКЦИЯ НАЗЫВАЕТСЯ, А НЕ СТИРАЕТСЯ. Здесь стояло
    ещё и ``assert UNSUPPORTED_IMAGE_MESSAGE in html``: текст отказа существовал
    ДВУМЯ копиями — сервер отдавал свою в ``detail``, а ручная загрузка в
    шаблоне показывала СВОЮ на любом ответе 400 и ``detail`` не читала вовсе, —
    и правило держало копии в step, потому что дисциплина их не удержала бы.
    Второй копии больше НЕТ: страница отказов не печатает, их печатает СТРОКА В
    ПОЛОСЕ у каждого отвергнутого файла. Держать в step константу саму с собой
    бессмысленно, и гарантия «человек читает точную причину» переехала на тест
    фрагмента полосы (``tests/test_pages/test_ads_image_upload.py``), а не
    исчезла. Импорт снят вместе с единственным своим читателем — см. шапку
    модуля.
    """
    response = await authed_client.get("/ads/new")

    assert response.status_code == 200
    html = response.text
    assert _attr_value(html, 'id="file-input"', "accept") == "image/jpeg,image/png"


@pytest.mark.asyncio
async def test_ads_edit_renders_own_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`GET /ads/{id}/edit` отдаёт 200 и РЕАЛЬНЫЕ данные объявления."""
    ad = await _seed_ad(db_session, title="Уникальный заголовок редактора")

    response = await authed_client.get(f"/ads/{ad.id}/edit")

    assert response.status_code == 200
    html = response.text
    assert "Уникальный заголовок редактора" in html
    assert "Полный текст объявления про осенний завоз" in html
    assert f'action="/ads/{ad.id}/edit"' in html


# --- T-02-04: владение объявлением ------------------------------------------


@pytest.mark.asyncio
async def test_ads_edit_foreign_ad_is_not_served(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужое объявление не открывается: редирект на список, а не 200.

    Закрепляет существующую проверку `Ad.user_id == user.id`
    (`app/pages/ads.py:151-156`) как регрессионный контракт — планы 02-04 и
    02-05 переписывают этот обработчик.
    """
    owner_id = (await _user(db_session)).id
    foreign = await _seed_ad(
        db_session, title="Чужое объявление", user_id=owner_id + 1000
    )

    response = await authed_client.get(
        f"/ads/{foreign.id}/edit", follow_redirects=False
    )

    assert response.status_code != 200
    assert response.status_code == 302
    assert response.headers["location"] == "/ads"


# --- T-02-02: базовый URL изображений берётся из настроек приложения --------


@pytest_asyncio.fixture
async def cdn_settings():
    """Настройки с узнаваемым S3-хостом, которого нет ни в одном `.env`."""
    return Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        s3_public_url="https://cdn.bound-to-app-settings.test/bucket",
    )


@pytest_asyncio.fixture
async def cdn_client(db_session, cdn_settings):
    app = create_app(settings=cdn_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: cdn_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": "testuser@test.com",
                "password": "testpass123",
                "name": "Test User",
            },
        )
        await c.post(
            "/login",
            data={"email": "testuser@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        yield c


@pytest.mark.asyncio
async def test_image_base_url_comes_from_app_settings(
    cdn_client: AsyncClient, db_session: AsyncSession
):
    """Ссылка на изображение строится из настроек ПРИЛОЖЕНИЯ, а не окружения.

    Ровно этот дефект (D-21): глобалы `get_image_url` / `s3_public_url` брали
    `get_settings()`, поэтому подмена зависимости `create_app(settings=...)` их
    не касалась, а базовый URL приезжал из `.env` рабочего каталога.
    """
    await _seed_ad(db_session, title="С картинкой", images=["u1/photo.jpg"])

    listing = await cdn_client.get("/ads")
    assert listing.status_code == 200
    assert (
        "https://cdn.bound-to-app-settings.test/bucket/u1/photo.jpg"
        in listing.text
    )


@pytest.mark.asyncio
async def test_editor_s3_public_url_global_comes_from_app_settings(
    cdn_client: AsyncClient, db_session: AsyncSession
):
    """Тот же контракт для глобала `s3_public_url()` в шаблоне редактора."""
    ad = await _seed_ad(db_session, title="С картинкой", images=["u1/photo.jpg"])

    response = await cdn_client.get(f"/ads/{ad.id}/edit")

    assert response.status_code == 200
    assert "https://cdn.bound-to-app-settings.test/bucket" in response.text


# --- Issue #40: интерфейс запрашивает МИНИАТЮРУ ------------------------------
#
# Плитка вложения рисуется в 96 px, аватарка карточки — в 32 px, а качается под
# них полноразмерный объект. Задача даёт интерфейсу отдельный лёгкий объект и
# оставляет полноразмерный адрес запасным — у вложений, загруженных ДО задачи,
# миниатюры нет и не появится (D-6).

CDN_BASE = "https://cdn.bound-to-app-settings.test/bucket"


def test_thumb_image_url_prefixes_a_stored_key():
    """Адрес миниатюры — базовый URL, слэш, приставка и ключ."""
    assert _thumb_image_url("7/photo.jpg", CDN_BASE) == f"{CDN_BASE}/thumbs/7/photo.jpg"


def test_thumb_image_url_rewrites_a_full_url_of_our_own_bucket():
    """Снимок в журнале отправок хранит АДРЕСА, а не ключи.

    `SendLog.ad_images` заполняется в `app/application/scheduling/use_cases.py`
    уже готовыми адресами — именно поэтому история и админка зовут
    `resolve_image_url`, а не `get_image_url`. Функция, знающая только про ключи,
    тихо оставила бы историю на полноразмерных картинках, и задача закрылась бы
    на трёх местах показа из пяти.
    """
    assert (
        _thumb_image_url(f"{CDN_BASE}/7/photo.jpg", CDN_BASE)
        == f"{CDN_BASE}/thumbs/7/photo.jpg"
    )


def test_thumb_image_url_leaves_a_foreign_url_alone():
    """Для чужого объекта миниатюры не существует, и выдумывать её нельзя.

    Приставка, приписанная к чужому адресу, дала бы ссылку на несуществующий
    объект в ЧУЖОМ хранилище: картинка пропала бы совсем, а запасной адрес вёл
    бы на неё же.
    """
    foreign = "https://images.example.org/bucket/7/photo.jpg"

    assert _thumb_image_url(foreign, CDN_BASE) == foreign


def test_thumb_image_url_of_empty_value_is_empty():
    assert _thumb_image_url("", CDN_BASE) == ""


@pytest.mark.asyncio
async def test_thumb_image_url_global_comes_from_app_settings(
    cdn_client: AsyncClient, db_session: AsyncSession
):
    """Новый глобал берёт базовый URL из настроек ПРИЛОЖЕНИЯ, как три прежних.

    Тот же контракт D-21: собери он `Settings()` сам, базовый URL приезжал бы из
    `.env` рабочего каталога мимо `create_app(settings=...)`.
    """
    await _seed_ad(db_session, title="С картинкой", images=["u1/photo.jpg"])

    listing = await cdn_client.get("/ads")

    assert listing.status_code == 200
    assert f"{CDN_BASE}/thumbs/u1/photo.jpg" in listing.text


@pytest.mark.asyncio
async def test_editor_tile_asks_for_the_thumbnail_and_declares_a_fallback(
    cdn_client: AsyncClient, db_session: AsyncSession
):
    """Элемент несёт ОБА адреса и однократный переключатель (D-6, P-8).

    Признака «миниатюра есть» нигде не хранится: форма `Ad.images` не менялась и
    меняться не должна. Поэтому механизм отката объявлен на самом элементе, а
    проверяется он наличием запасного адреса и обработчика, а не обращением к
    хранилищу — обращение на каждую картинку в списке и есть то, чего задача
    избегает.
    """
    ad = await _seed_ad(db_session, title="С картинкой", images=["u1/photo.jpg"])

    response = await cdn_client.get(f"/ads/{ad.id}/edit")

    assert response.status_code == 200
    html = response.text
    tile = html[html.index('<div data-media') : html.index("</div>", html.index('<div data-media'))]
    assert f'src="{CDN_BASE}/thumbs/u1/photo.jpg"' in tile
    assert f'data-full="{CDN_BASE}/u1/photo.jpg"' in tile
    # Снятие обработчика с самого себя — защита от цикла, а не микрооптимизация:
    # без него отказ ЗАПАСНОГО адреса запускал бы бесконечное переключение.
    assert "onerror=" in tile
    assert "this.onerror=null" in tile


# ⚠️ ДВА ПРАВИЛА ЗДЕСЬ СНЯТЫ ВМЕСТЕ СО СВОИМ ПРЕДМЕТОМ (D-12 Фазы 12, план
# 12-03), И ОБА НАЗЫВАЮТСЯ, А НЕ ИСЧЕЗАЮТ МОЛЧА.
#
# (1) `test_editor_javascript_carries_the_thumbnail_prefix` держал в step ВТОРУЮ
#     КОПИЮ правила сборки адреса миниатюры: плитки строил клиент, макросом
#     воспользоваться не мог, и приставка существовала в скрипте отдельным
#     объявлением. Плитки печатает СЕРВЕР макросом `components/thumb.html`,
#     второй копии в скрипте больше нет, и приставки там нет тоже — правило
#     утверждало бы присутствие того, чего не существует. Первая копия при этом
#     проверяется как и прежде: соседнее
#     `test_editor_tile_asks_for_the_thumbnail_and_declares_a_fallback` читает
#     ОТРЕНДЕРЕННУЮ плитку и требует оба адреса и однократный переключатель.
#
# (2) `test_editor_upload_handler_reads_the_refusal_from_the_response_body`
#     (issue #40, P-9) требовал, чтобы обработчик загрузки читал причину из тела
#     ответа, а не показывал свою копию на любом отказе. Обработчика больше нет:
#     причина приезжает СТРОКОЙ В ПОЛОСЕ, своя у каждого отвергнутого файла
#     (D-05), и печатает её сервер. Предмет правила — клиентский разбор ответа —
#     не изменился к лучшему, а перестал существовать; утверждение о нём
#     зеленело бы или краснело бы на чём угодно, кроме своего предмета.
#     Гарантия, ради которой правило заводилось, переехала на тест фрагмента
#     полосы в `tests/test_pages/test_ads_image_upload.py`.


# --- План 02-04, ADS-04: черновик создаётся автосохранением ------------------
#
# Ключевое свойство раздела — сохранение НЕ перерисовывает форму. Проверить это
# можно только по телу ответа: страница с перерисованной формой тоже отдаёт 200,
# и пользователь узнаёт о поломке, лишь потеряв каретку на середине текста.


@pytest.mark.asyncio
async def test_ads_new_page_creates_no_row(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-03: заход на `/ads/new` не создаёт запись.

    Иначе каждое случайное открытие раздела оставляло бы в списке пустое
    объявление, и пользователь чистил бы за интерфейсом.
    """
    owner_id = (await _user(db_session)).id
    before = await _ads_count(db_session, owner_id)

    response = await authed_client.get("/ads/new")

    assert response.status_code == 200
    assert await _ads_count(db_session, owner_id) == before


@pytest.mark.asyncio
async def test_autosave_creates_draft_and_pushes_edit_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-03: первое автосохранение создаёт черновик и подменяет адрес."""
    owner_id = (await _user(db_session)).id

    response = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик из автосохранения", text="Набранный текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    ad = await _only_ad(db_session, owner_id)
    assert ad.status == AD_STATUS_DRAFT
    assert response.headers.get("HX-Push-Url") == f"/ads/{ad.id}/edit"


@pytest.mark.asyncio
async def test_created_draft_keeps_the_push_url_header_after_the_move_to_the_response_layer(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-13 Фазы 11: заголовок истории переживает переезд на слой ответа.

    ⚠️ ПРЕДМЕТ — ЗАГОЛОВОК НА ВОЗВРАЩАЕМОМ ОТВЕТЕ, А НЕ КОД ОБРАБОТЧИКА.
    Утверждение снимается с `response.headers`, потому что предмет вопроса —
    что доезжает до БРАУЗЕРА. Прочтение исходника сказало бы, что заголовок
    где-то ставится, и промолчало бы о том, на ТОТ ли объект: сборщик фрагмента
    вправе построить один ответ, а вернуть другой, и подмена адреса тихо
    пропала бы. Цена потери названа величиной: следующее автосохранение ушло бы
    на `/ads/new` со СТАРЫМ (пустым) скрытым полем и завело бы ВТОРОЙ черновик.

    ⚠️ НАБЛЮДЕНИЕ D-13 ЗАПИСАНО ЗДЕСЬ ЦЕЛИКОМ, ПОТОМУ ЧТО ОНО ЕСТЬ ПРЕДМЕТ
    ПУНКТА РОАДМАПА О СОВМЕСТНОМ ПОВЕДЕНИИ. Атрибут разметки `hx-push-url` фаза
    не ставит НИ НА ОДНУ форму (решение по каждой форме — QUAL-04, Фаза 15),
    поэтому совместного поведения атрибута и заголовка в проекте сегодня НЕТ:
    адрес в строке меняет только заголовок. Приоритет их, если атрибут появится,
    измерен по вендоренному рантайму (htmx 2.0.10, функция `Mn`): заголовок
    ответа читается ПЕРВЫМ, атрибут — только при его отсутствии. Проверять это
    сегодня нечем и незачем — второй стороны совмещения не существует, — и
    именно это отсутствие здесь записано, а не выведено.

    Четыре утверждения, и ни одно не выводится из остальных: заголовок на
    ПЕРВОМ сохранении есть; на ВТОРОМ (когда запись уже создана) его НЕТ —
    иначе адрес переписывался бы на каждом нажатии клавиши; без htmx первое
    сохранение по-прежнему 302 в редактор, а «Сохранить» — 302 в список.
    """
    owner_id = (await _user(db_session)).id

    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик слоя ответа", text="Набранный текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200
    created = await _only_ad(db_session, owner_id)
    assert first.headers.get("HX-Push-Url") == f"/ads/{created.id}/edit", (
        "заголовок истории НЕ приехал на ответе создания черновика: адрес в "
        "строке остался бы `/ads/new`, и следующее автосохранение завело бы "
        f"второй черновик (снято: {first.headers.get('HX-Push-Url')!r})"
    )

    second = await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Второй вариант",
            text="Набранный текст",
            extra=[("ad_id", str(created.id))],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert second.status_code == 200
    assert "HX-Push-Url" not in second.headers, (
        "заголовок истории приехал на ОБНОВЛЕНИИ: адрес в строке уже верен, и "
        "повторная запись истории плодила бы состояния браузера на каждом "
        f"срабатывании автосохранения (снято: {second.headers.get('HX-Push-Url')!r})"
    )

    # Путь без JavaScript не тронут переездом ни одним из двух своих исходов.
    degraded_first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик без JavaScript", text="Текст"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    assert degraded_first.status_code == 302
    degraded_ad = (
        await db_session.execute(
            select(Ad).where(Ad.user_id == owner_id).order_by(Ad.id.desc())
        )
    ).scalars().first()
    assert degraded_first.headers["location"] == f"/ads/{degraded_ad.id}/edit"

    saved = await authed_client.post(
        f"/ads/{degraded_ad.id}/edit",
        content=form_body(
            title="Черновик без JavaScript", text="Текст", extra=[("save", "1")]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    assert saved.status_code == 302
    assert saved.headers["location"] == "/ads"


@pytest.mark.asyncio
async def test_autosave_response_carries_no_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Форма при автосохранении НЕ перерисовывается.

    Любая подмена, накрывающая поле ввода, сбрасывает каретку и выделение:
    пользователь физически не сможет набрать длинный текст.
    """
    response = await authed_client.post(
        "/ads/new",
        content=form_body(),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert 'id="ad-form"' not in response.text
    assert "<form" not in response.text


@pytest.mark.asyncio
async def test_autosave_response_updates_three_blocks(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-06: один ответ обновляет предпросмотр, сводку и индикатор."""
    response = await authed_client.post(
        "/ads/new",
        content=form_body(),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text
    assert 'id="ad-preview"' in html
    assert 'id="ad-summary"' in html
    assert 'id="autosave-indicator"' in html
    assert "hx-swap-oob" in html


@pytest.mark.asyncio
async def test_a_removal_deletes_only_the_removed_tile(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-10 Фазы 12: убранное вложение обязано исчезнуть С ЭКРАНА, а не только из базы.

    Кнопка «×» — именованная кнопка отправки ФОРМЫ ОБЪЯВЛЕНИЯ (перехват снят
    планом 12-03), а форма несёт ``hx-swap="none"``: своего места подмены у
    ответа нет вовсе, и всё обновление приезжает внеполосно. Без блока снятия
    ключ уходил бы из базы, а плитка оставалась бы на экране до перезагрузки.

    ⚠️ ПРАВИЛО ИНВЕРТИРОВАНО ВВЕРХ ВМЕСТЕ С ПРЕДМЕТОМ, А НЕ ПЕРЕПИСАНО (Фаза 12,
    план 12-11, D-19; идиома плана 12-08). ПРЕЖНЯЯ РЕДАКЦИЯ НАЗЫВАЕТСЯ. Прежде
    правило звалось ``test_autosave_response_carries_the_media_tray`` и
    требовало УЗЕЛ ПОЛОСЫ ``#media-tray`` с признаком внеполосной подмены; оно
    было верно для дерева, на котором писалось. Предмет — «убранное кнопкой «×»
    исчезает с экрана» — НЕ ОТМЕНЁН, а УСИЛЕН: подмена узла ЦЕЛИКОМ заявляла
    власть над ВСЕМ его содержимым, включая ключи, которых этот запрос не
    видел. Замер верификатора (зонд WR-07, ПОРЯДОК II): ``C present in removal
    tray: False`` при ``s3 calls: 2`` — ключ, уже записанный летящей загрузкой
    в хранилище, уносился из документа БЕЗ единой строки. Теперь ответ несёт по
    одному блоку АДРЕСНОГО СНЯТИЯ на убранный ключ и адресует РОВНО тот ключ,
    который этот запрос действительно видел.

    ⚠️ ЛЕТОПИСЬ ПЕРЕНАЦЕЛИВАНИЯ ПЛАНА 12-07 СОХРАНЕНА. Ещё прежде запрос шёл БЕЗ
    ``remove_image``, то есть правило измеряло «полоса приезжает КАЖДЫМ
    автосохранением» — а ровно это и есть гап 2 верификации: ответ,
    перерисовывающий полосу из базы, отстающей от документа на незаписанный
    ключ, уносил с экрана и свежую плитку, и строки отказа, за которые D-04
    заплатил лживым кодом 200. Соседнее правило
    ``test_a_text_only_autosave_leaves_the_tray_alone`` сторожит вторую
    половину: автосохранение, состава вложений не менявшее, ни полосы, ни блока
    снятия не приносит вовсе.

    ⚠️ СУДЬБА ПРЕЖНЕГО УТВЕРЖДЕНИЯ О СКРЫТОМ ПОЛЕ ОСТАВШЕГОСЯ КЛЮЧА НАЗЫВАЕТСЯ
    ОТДЕЛЬНОЙ СТРОКОЙ. Прежде правило требовало, чтобы поле оставшегося ключа
    приехало ВНУТРИ внеполосной полосы. Теперь ответ не несёт полей
    ``name="images"`` ВОВСЕ — и оставшийся ключ живёт в документе КРЕПЧЕ, чем
    прежде, потому что ответ его УЗЛА НЕ ТРОГАЕТ: он не переиздаётся, а значит
    и не может быть переиздан из отстающей базы.

    ⚠️ ПОСЛЕДНЕЕ УТВЕРЖДЕНИЕ ЗАМЕНЯЕТ ДЕЙСТВУЮЩЕЕ, И ЗАМЕНА НАЗЫВАЕТСЯ, А НЕ
    ДЕЛАЕТСЯ МОЛЧА. Прежде утверждалось отсутствие убранного ключа как СТРОКИ
    где угодно в ответе (``f'value="{dropped}"' not in html``). Предмет, который
    та строка охраняла, — «убранный ключ не возвращается в документ как
    ПРИКРЕПЛЯЕМОЕ состояние», то есть как значение поля, которое
    ``_save_from_editor`` прочитает в ``ad.images``. Ровно это утверждается
    теперь, и утверждается СИЛЬНЕЕ: полей ``name="images"`` ответ не несёт ни
    одного, а не только не несёт одного названного значения. Снимается ровно
    одна грань — власть над ключом как над произвольной ПОДСТРОКОЙ ответа, — и
    причина снятия прямая: план 12-12 ЭТОЙ ЖЕ ПАРТИИ заводит ВЫЧИТАЮЩУЮ метку
    ``removed_images``, несущую ровно этот ключ ровно ради того, чтобы он НЕ
    вернулся. Бессрочный запрет на ключ-подстроку краснел бы на ПРАВИЛЬНОЙ
    работе, меряя ИМЯ ПОЛЯ вместо судьбы ключа.

    Снятую грань подхватывает партия, и подхватывает ПРАВИЛАМИ, а не
    рассуждением. План 12-12 задачей 1 заводит пару:
    ``test_a_marked_key_does_not_come_back_through_a_stale_snapshot`` — ключ не
    воскресает в базе; ``test_the_removal_mark_is_the_only_place_the_removed_key
    _comes_back`` — единственное место возврата ключа в ответе есть вычитающая
    метка, и это ЗАМЕРЕНО. ⚠️ НА ДЕРЕВЕ ПОСЛЕ ЭТОГО ПЛАНА ВТОРОГО ПРАВИЛА ЕЩЁ
    НЕТ: оно названо здесь ОБЯЗАТЕЛЬСТВОМ ПАРТИИ, а не действующим фактом.
    """
    owner_id = (await _user(db_session)).id
    kept = image_key(owner_id, "p0.jpg")
    dropped = image_key(owner_id, "p1.jpg")
    ad = await _seed_ad(db_session, title="С вложением", images=[kept, dropped])

    response = await authed_client.post(
        f"/ads/{ad.id}/edit",
        content=form_body(
            title="С вложением",
            text="Текст",
            images=[kept, dropped],
            extra=[("remove_image", dropped)],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text
    assert 'hx-swap-oob="delete"' in html, (
        "ответ убирания не принёс ни одного блока СНЯТИЯ: убранная кнопкой «×» "
        "плитка останется на экране, хотя ключ из базы уже ушёл — человек "
        "нажмёт ещё раз"
    )
    assert removed_dom_ids(html) == [media_dom_id(dropped)], (
        f"к снятию названы {removed_dom_ids(html)} вместо "
        f"[{media_dom_id(dropped)!r}]: ответ адресует не ту плитку, которую "
        "убрал этот запрос, — либо уносит чужую, либо не уносит ничего"
    )
    assert 'id="media-tray"' not in html, (
        "ответ убирания принёс УЗЕЛ ПОЛОСЫ: внеполосная подмена заменит его "
        "ЦЕЛИКОМ и заявит власть над ключами, которых этот запрос не видел — "
        "ключ, записанный летящей загрузкой, исчезнет с экрана без единой "
        "строки (зонд WR-07, ПОРЯДОК II)"
    )
    # (1) НУЛЕВОЙ СЧЁТ — над ИМЕНЕМ поля, см. абзац у `removed_dom_ids`.
    assert html.count('name="images"') == 0, (
        f"ответ убирания несёт полей вложений {html.count('name=\"images\"')} "
        "вместо нуля: оставшиеся ключи он своей властью не видел, и "
        "переиздавать их из отстающей базы не вправе"
    )
    # (2) ЗНАЧЕНИЯ — образцом полного набора атрибутов, инструмент ДРУГОЙ.
    assert dropped not in HIDDEN_KEY_FIELD.findall(html), (
        "убранный ключ вернулся в документ ПРИКРЕПЛЯЕМЫМ состоянием: следующая "
        "отправка формы записала бы его в объявление обратно, и человек нажал "
        "бы «×» ещё раз"
    )


# --- ПОРЯДОК I зонда WR-07: документ помнит убирание (план 12-12, D-19) ------


@pytest.mark.asyncio
async def test_a_marked_key_does_not_come_back_through_a_stale_snapshot(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПОРЯДОК I зонда WR-07: убранный ключ не воскресает ОТСТАЮЩИМ СНИМКОМ.

    ⚠️ ОТКУДА ВО ВТОРОМ ЗАПРОСЕ БЕРЁТСЯ СТАРЫЙ СНИМОК — ЭТО НЕ ВЫДУМКА ПРАВИЛА,
    А ЗАМЕР ВЕРИФИКАТОРА. Человек выбрал крупный файл и, пока загрузка летела,
    нажал «×». Ответ загрузки пришёл ПОСЛЕДНИМ и подменой содержимого полосы
    переиздал в документ снимок скрытых полей, снятый ДО убирания: плитка
    убранного ключа вернулась на экран. Тем же ответом уезжает заголовок
    ``HX-Trigger-After-Swap: ads-image-attached``, форма объявления слушает его
    ``from:body`` и немедленно уходит автосохранением — с ТЕМ САМЫМ старым
    снимком. Замер дословно: ``deleted key A resurrected in db: True``. Удаление,
    которое человек СДЕЛАЛ, отменено молча.

    ⚠️ СЕРВЕР РАЗЛИЧИТЬ ЭТИ ДВА СЛУЧАЯ ПО ОДНОМУ СНИМКУ НЕ МОЖЕТ, И ИМЕННО
    ПОЭТОМУ ПОМНИТЬ ОБЯЗАН ДОКУМЕНТ. Ключ, пришедший в снимке и отсутствующий в
    базе, — это либо только что загруженный (законный), либо воскресший убранный
    (отменяющий действие человека). Решение владельца **D-19** отвергло (а)
    общую очередь двух форм («×» ждал бы декодирования, пережатия и двух кругов
    к хранилищу) и (б) запись допущением — и оставило механизм планировщику.
    Механизм: метка убирания живёт в документе ВНЕ цели подмены формы загрузки,
    переживает переиздание снимка и вычитается на сохранении.

    ⚠️ МЕТКА БЕРЁТСЯ ИЗ ОТВЕТА, А НЕ ПОДСТАВЛЯЕТСЯ ТЕСТОМ (см. ``removal_marks``).
    Правило противоположного порядка — ``test_order_ii_a_stored_key_is_not_
    carried_out_by_the_removal`` в ``tests/test_pages/test_ads_image_upload.py``;
    пара меряет СУДЬБУ КЛЮЧА на обоих чередованиях, а не равенство строк.
    """
    owner_id = (await _user(db_session)).id
    kept = image_key(owner_id, "p0.jpg")
    dropped = image_key(owner_id, "p1.jpg")
    # Идентификатор снимается ДО истечения сессии: после `expire_all` обращение
    # к полю посеянного объекта уехало бы ленивой подгрузкой в синхронном
    # контексте и уронило бы правило отказом драйвера вместо утверждения.
    ad_id = (await _seed_ad(db_session, title="С вложением", images=[kept, dropped])).id

    removal = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="С вложением",
            text="Текст",
            images=[kept, dropped],
            extra=[("remove_image", dropped)],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert removal.status_code == 200
    assert removal_marks(removal.text) == [dropped], (
        f"ответ убирания принёс метки {removal_marks(removal.text)} вместо "
        f"[{dropped!r}]: документу нечем помнить действие человека, и снимок, "
        "переизданный ответом загрузки, вернёт убранный ключ в базу"
    )
    mark = removal_marks(removal.text)[0]

    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == [kept], (
        f"после убирания в базе {stored.images} вместо [{kept!r}]: дальше мерить "
        "воскресение нечему"
    )

    # ВТОРОЕ сохранение — то самое, которое заказывает заголовок ответа
    # загрузки: снимок СТАРЫЙ (оба ключа), метка ПЕРЕЖИЛА подмену.
    resurrection = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="С вложением",
            text="Текст",
            images=[kept, dropped],
            extra=[(REMOVAL_MARK_FIELD_NAME, mark)],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert resurrection.status_code == 200
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == [kept], (
        f"в базе {stored.images} вместо [{kept!r}]: убранное человеком вложение "
        "воскресло отстающим снимком — удаление, которое он СДЕЛАЛ, отменено "
        "молча (зонд WR-07, ПОРЯДОК I)"
    )
    assert media_dom_id(dropped) in removed_dom_ids(resurrection.text), (
        f"к снятию названы {removed_dom_ids(resurrection.text)}: воскресшая "
        f"чужой гонкой плитка {media_dom_id(dropped)!r} осталась на экране, и "
        "человек смотрит на плитку, за которой нет ключа"
    )


@pytest.mark.asyncio
async def test_a_mark_is_subtracted_before_the_ownership_check(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Метка вычитается ДО сверки владения — порядок несущий, а не косметический.

    ⚠️ ОТКАЗ ПО ДЛИНЕ СТОИ́Т В ``own_image_keys`` ПЕРВЫМ. Вычитание, поставленное
    ПОСЛЕ сверки, означало бы, что воскресший чужой гонкой ключ переполняет
    потолок — и человек получает отказ 400 за гонку, которой не устраивал:
    он убрал вложение, освободив место, а сервер отвечает «вложений больше N».

    Вычитание при этом не трогает ни предиката принадлежности, ни потолка:
    ``own_image_keys`` остаётся ЕДИНСТВЕННЫМ местом, где решается «мой ли ключ»
    и где потолок отказывает (D-07, Hyrum).
    """
    owner_id = (await _user(db_session)).id
    limit = test_settings.max_images_per_ad
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(limit + 1)]
    # Идентификатор снимается ДО истечения сессии — по той же причине, что и у
    # соседнего правила выше.
    ad_id = (await _seed_ad(db_session, title="На потолке", images=[])).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="На потолке",
            text="Текст",
            images=keys,
            extra=[(REMOVAL_MARK_FIELD_NAME, keys[0])],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "вложений больше" not in response.text, (
        "ответ несёт отказ по ДЛИНЕ: метка вычтена ПОСЛЕ сверки владения, и "
        "воскресший чужой гонкой ключ переполнил потолок — человек получил "
        "отказ за гонку, которой не устраивал"
    )

    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == keys[1:], (
        f"в базе {stored.images} вместо {keys[1:]}: снимок длиной на единицу "
        "больше потолка, из которого один ключ ПОМЕЧЕН, обязан сохраниться — "
        "вычитание стои́т ДО сверки владения"
    )


@pytest.mark.asyncio
async def test_the_removal_mark_is_the_only_place_the_removed_key_comes_back(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Убранный ключ возвращается в ответ РОВНО ОДНИМ местом — вычитающей меткой.

    ⚠️ ЭТО ПРАВИЛО СУЩЕСТВУЕТ РАДИ ОСИ, СНЯТОЙ СОСЕДНИМ ПЛАНОМ ПАРТИИ, И
    ОСТАВЛЯТЬ ЕЁ РАССУЖДЕНИЕМ БЫЛО НЕЛЬЗЯ. Правило
    ``test_a_removal_deletes_only_the_removed_tile`` (план 12-11) сузило своё
    утверждение об убранном ключе: прежде оно требовало отсутствия ключа как
    ПРОИЗВОЛЬНОЙ ПОДСТРОКИ ответа, теперь — отсутствия его среди значений полей
    ``name="images"``. На СВОЕЙ оси новая форма СИЛЬНЕЕ: полей вложений ответ не
    несёт НИ ОДНОГО, а не только не несёт одного названного значения. Сужение
    сделано ровно потому, что ЭТОТ план возвращает ключ в тот же ответ
    ВЫЧИТАЮЩЕЙ меткой, и бессрочный запрет на ключ-подстроку краснел бы на
    правильной работе.

    Честным сужение остаётся ровно настолько, насколько ЗАМЕРЕНО, что возврат
    ограничен меткой. Замеряет это ДАННОЕ правило, и ни одно утверждение правила
    12-11 при этом не правится: оно уже написано в форме, которую метка не
    краснит.
    """
    owner_id = (await _user(db_session)).id
    kept = image_key(owner_id, "p0.jpg")
    dropped = image_key(owner_id, "p1.jpg")
    ad = await _seed_ad(db_session, title="С вложением", images=[kept, dropped])

    response = await authed_client.post(
        f"/ads/{ad.id}/edit",
        content=form_body(
            title="С вложением",
            text="Текст",
            images=[kept, dropped],
            extra=[("remove_image", dropped)],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text

    # (1) Полей вложений в ответе нет ни одного — утверждение 12-11, повторённое
    # здесь затем, чтобы «возврат ограничен меткой» мерилось ОДНИМ правилом
    # целиком, а не собиралось читателем из двух файлов.
    assert html.count('name="images"') == 0, (
        f"ответ убирания несёт полей вложений {html.count('name=\"images\"')} "
        "вместо нуля: метка перестала быть ЕДИНСТВЕННЫМ местом возврата ключа"
    )

    # (2) Все вхождения значения убранного ключа принадлежат полю метки, и
    # таких вхождений ОДНО.
    assert html.count(dropped) == 1, (
        f"значение убранного ключа встречается в ответе {html.count(dropped)} "
        "раз вместо одного: сужение утверждения плана 12-11 перестало быть "
        "честным — ключ возвращается не только вычитающей меткой"
    )
    assert dropped not in _MARK_FIELD_TAG.sub("", html), (
        "убранный ключ встречается в ответе ВНЕ поля метки: возврат ключа "
        "перестал быть ограничен вычитанием, и ось, снятая планом 12-11, "
        "осталась незамеренной"
    )

    # (3) Имя поля метки читается ИЗ ОТВЕТА и не равно имени поля вложений:
    # путь ВВОДА ключа в состав вложений метка не открывает даже по написанию.
    mark_tags = [tag for tag in _ANY_TAG.findall(html) if f'value="{dropped}"' in tag]
    assert len(mark_tags) == 1, (
        f"тегов, несущих значение убранного ключа, {len(mark_tags)} вместо "
        "одного: имя поля метки читать неоткуда"
    )
    mark_name = _TAG_NAME.search(mark_tags[0])
    assert mark_name is not None, (
        f"тег {mark_tags[0]!r} несёт значение убранного ключа и не несёт имени "
        "поля: такое поле форма не отправит, и метка не доедет до сохранения"
    )
    assert mark_name.group(1) == REMOVAL_MARK_FIELD_NAME != "images", (
        f"имя поля метки {mark_name.group(1)!r}: оно обязано быть "
        f"{REMOVAL_MARK_FIELD_NAME!r} и обязано отличаться от имени поля "
        "вложений — иначе тот же ответ открыл бы путь ВВОДА ключа в состав "
        "вложений по одному написанию (T-12-12-02)"
    )


@pytest.mark.asyncio
async def test_a_text_only_autosave_leaves_the_tray_alone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Гап 2 Фазы 12: автосохранение, вложений не менявшее, полосы НЕ приносит.

    ⚠️ ЭТО ПРАВИЛО ОБ ОТСУТСТВИИ, И ОТСУТСТВИЕ ЗДЕСЬ — СВОЙСТВО, А НЕ ЭКОНОМИЯ
    БАЙТОВ. Внеполосная подмена заменяет узел ЦЕЛИКОМ, а полоса после плана
    12-03 есть ЕДИНСТВЕННЫЙ источник списка ключей в документе. Ответ
    автосохранения рисует её ИЗ БАЗЫ, и база отстаёт от документа ровно на то,
    что человек только что прикрепил и что сервер ещё не записал: свежую плитку
    и строки отказа смешанной партии. Автосохранение при этом заказывает сама же
    загрузка — заголовок ``HX-Trigger-After-Swap: ads-image-attached`` поднимает
    слушатель формы объявления, — поэтому причина отказа не доживала до второго
    взгляда на экран.

    Поэтому перерисовка полосы становится ИСКЛЮЧЕНИЕМ, которое надо заслужить
    изменением состава вложений, а не умолчанием, которое стирает. Прочие
    внеполосные блоки ответа при этом на месте — правило утверждает и это,
    иначе зеленело бы на ответе, сломанном целиком.
    """
    owner_id = (await _user(db_session)).id
    key = image_key(owner_id, "p0.jpg")
    ad = await _seed_ad(db_session, title="С вложением", images=[key])

    response = await authed_client.post(
        f"/ads/{ad.id}/edit",
        content=form_body(title="С вложением", text="Текст правки", images=[key]),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text
    assert 'id="media-tray"' not in html, (
        "автосохранение, состава вложений НЕ менявшее, всё-таки принесло узел "
        "полосы: внеполосная подмена заменит её целиком и унесёт с экрана то, "
        "чего база ещё не знает, — свежую плитку и строку отказа"
    )
    assert 'id="ad-preview"' in html, (
        "вместе с полосой из ответа пропал предпросмотр: правило требовало "
        "убрать ОДИН блок, а не сломать ответ целиком"
    )
    assert 'id="autosave-indicator"' in html, (
        "вместе с полосой из ответа пропал индикатор автосохранения: человек "
        "перестанет видеть, сохранилась ли его правка"
    )


@pytest.mark.asyncio
async def test_plain_post_without_htmx_redirects(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: базовый путь без JavaScript отвечает редиректом, а не фрагментом."""
    ad = await _seed_ad(db_session, title="Объявление без JavaScript")

    response = await authed_client.post(
        f"/ads/{ad.id}/edit",
        content=form_body(title="Правка без JavaScript", text="Текст"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302


# --- План 02-08, CR-01: повторное автосохранение адресуется в ту же запись ---
#
# Прежний тест этого места (`test_repeated_autosave_updates_the_same_ad`) слал
# второй запрос на `/ads/{id}/edit` — на адрес, который форма НЕ несёт и на
# который браузер не уходит: `hx-post` неизменяем, а `hx-swap="none"` гарантирует,
# что форма никогда не перерисуется. Тест утверждал переписывание адреса, которого
# никто не выполняет, и был зелёным ровно тогда, когда пользователь терял правки
# (02-REVIEW.md, IN-06). Он удалён; ниже адрес второго запроса берётся из ответа.


@pytest.mark.asyncio
async def test_repeated_autosave_posts_to_the_url_the_form_carries(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Второе автосохранение на АДРЕС ФОРМЫ обновляет первый черновик.

    Ключевое отличие от удалённого теста: адрес второго запроса не назначается,
    а сверяется с атрибутом `hx-post`, который сервер отдал в разметке формы.
    Пока эти два адреса совпадают, тест меряет то же, что делает браузер.
    """
    owner_id = (await _user(db_session)).id

    page = await authed_client.get("/ads/new")
    assert page.status_code == 200
    assert _attr_value(page.text, 'id="ad-form"', "hx-post") == "/ads/new"

    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Первый вариант", text="Текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200
    ad_id = _ad_id_from(first.text)
    assert ad_id, "ответ автосохранения не назвал созданную запись"

    second = await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Второй вариант", text="Текст", extra=[("ad_id", ad_id)]
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert second.status_code == 200
    assert await _ads_count(db_session, owner_id) == 1
    stored = await _only_ad(db_session, owner_id)
    assert stored.title == "Второй вариант"
    assert stored.status == AD_STATUS_DRAFT, "автосохранение изменило состояние"


@pytest.mark.asyncio
async def test_creation_path_keeps_text_and_attachment_in_one_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-05, SC-2: текст и вложение с пути СОЗДАНИЯ лежат в ОДНОМ объявлении.

    Загрузка файла поднимает событие `change`, htmx уходит на тот же `/ads/new`,
    и до этого плана вложение приезжало во ВТОРУЮ запись — набранный текст
    оставался в первой.
    """
    owner_id = (await _user(db_session)).id

    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик с вложением", text="Набранный текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200
    ad_id = _ad_id_from(first.text)
    key = image_key(owner_id, "photo.jpg")

    second = await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Черновик с вложением",
            text="Набранный текст",
            images=[key],
            extra=[("ad_id", ad_id)],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert second.status_code == 200
    assert await _ads_count(db_session, owner_id) == 1
    stored = await _only_ad(db_session, owner_id)
    assert stored.text == "Набранный текст"
    assert stored.images == [key]


@pytest.mark.asyncio
async def test_save_during_autosave_overlap_lands_in_one_published_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """CR-04, SC-1/SC-2: «Сохранить» поверх летящего автосохранения — одна запись.

    Тест закрепляет семантику ОЧЕРЕДИ (`hx-sync="this:queue last"`): поставленный
    в очередь запрос сериализуется из живой формы ПОСЛЕ обработки ответа первого,
    когда внеполосная подмена уже вписала идентификатор созданного черновика в
    #ad-id-field, — поэтому он несёт этот идентификатор и уходит путём
    обновления. Прежняя стратегия отмены выбрасывала ответ вместе с
    идентификатором: заменяющий запрос сериализовался с ПУСТЫМ скрытым полем,
    уходил в ветку создания, и на руках оставались сирота-черновик с ранним
    текстом плюс опубликованный дубль — молчаливая потеря работы, запрещённая
    планом 02-08.
    """
    owner_id = (await _user(db_session)).id

    # (1) Автосохранение в полёте: путь создания, скрытое поле ещё пустое.
    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик", text="текст до нажатия"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200

    # (2) Идентификатор извлекается из ТЕЛА ответа — из внеполосного блока
    # #ad-id-field (autosave_response.html): ровно так браузер подменяет поле
    # ДО того, как очередь переиздаст следующий запрос.
    ad_id = _ad_id_from(first.text)
    assert ad_id, "ответ автосохранения не назвал созданную запись"

    # (3) Поставленный в очередь запрос — сериализация ЖИВОЙ формы после
    # подмены: явное «Сохранить» с текстом на момент нажатия и двумя ключами
    # вложений (путь requestSave() после загрузки — тот же триггер той же
    # формы, SC-2).
    keys = [image_key(owner_id, "p0.jpg"), image_key(owner_id, "p1.jpg")]
    second = await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Черновик",
            text="текст на момент нажатия",
            images=keys,
            extra=[("ad_id", ad_id), ("save", "1")],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert second.status_code == 200

    # (4) РОВНО одна строка ads: published, текст и вложения ВТОРОЙ
    # сериализации, порядок ключей сохранён.
    stored = await _only_ad(db_session, owner_id)
    assert stored.status == AD_STATUS_PUBLISHED
    assert stored.text == "текст на момент нажатия"
    assert stored.images == keys


@pytest.mark.asyncio
async def test_body_ad_id_from_another_user_is_refused(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02G-01: идентификатор из ТЕЛА запроса не открывает чужую запись.

    Этот план вводит в тело `/ads/new` новый идентификатор объекта, то есть
    расширяет границу доверия. Неподтверждённое владение обязано давать отказ —
    ни записи в чужую строку, ни создания нового черновика взамен.
    """
    owner_id = (await _user(db_session)).id
    # Идентификаторы снимаются СРАЗУ: каждый последующий commit сбрасывает
    # загруженные атрибуты, и обращение к ним из синхронного кода теста ушло бы
    # в ленивую подгрузку вне greenlet-а.
    stranger_id = (await _stranger(db_session)).id
    foreign_id = (
        await _seed_ad(db_session, title="Чужое объявление", user_id=stranger_id)
    ).id
    before = await _ads_count(db_session, owner_id)

    await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Захват", text="Захват", extra=[("ad_id", str(foreign_id))]
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    db_session.expire_all()
    stored = (
        await db_session.execute(select(Ad).where(Ad.id == foreign_id))
    ).scalar_one()
    assert stored.title == "Чужое объявление"
    assert await _ads_count(db_session, stranger_id) == 1
    assert await _ads_count(db_session, owner_id) == before


@pytest.mark.asyncio
async def test_plain_post_without_htmx_still_redirects(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: базовый путь БЕЗ JavaScript на `/ads/new` по-прежнему отвечает 302.

    Регрессия к задаче 2: маршрутизация тела запроса на обновление не имеет
    права превратить обычную отправку формы в фрагмент.
    """
    response = await authed_client.post(
        "/ads/new",
        content=form_body(title="Без JavaScript", text="Текст"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302


@pytest.mark.asyncio
async def test_preview_renders_stored_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-06: предпросмотр показывает записанный текст, а не пустую рамку."""
    response = await authed_client.post(
        "/ads/new",
        content=form_body(title="Заголовок", text="Уникальный текст предпросмотра"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "Уникальный текст предпросмотра" in response.text


@pytest.mark.asyncio
async def test_preview_never_shows_rejected_attachments(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """D-10: предпросмотр рендерится из БАЗЫ, а не из тела запроса.

    Сервер отклоняет сохранение с числом вложений сверх лимита (D-13). Превью,
    собранное из формы, показало бы отклонённое — то есть пообещало бы отправку
    того, чего в базе нет.
    """
    owner_id = (await _user(db_session)).id
    kept = image_key(owner_id, "kept.jpg")
    ad = await _seed_ad(db_session, title="С вложением", images=[kept])
    ad_id = ad.id
    rejected = [
        image_key(owner_id, f"over{i}.jpg")
        for i in range(test_settings.max_images_per_ad + 1)
    ]

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Слишком много", text="Текст", images=rejected),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    for value in rejected:
        assert value not in response.text
    assert "autosave--error" in response.text
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == [kept]
    assert stored.title == "С вложением"


@pytest.mark.asyncio
async def test_preview_lists_every_attachment_in_send_order(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-06, UI-SPEC E9 `zero-one-many`: предпросмотр показывает ВСЕ вложения.

    Макет рисует ровно один медиаблок, раскладка 2…10 вложений им не задана.
    Дефолт контракта — переносящаяся строка миниатюр в порядке отправки, то есть
    в порядке `Ad.images`. Порядок проверяется ПОЗИЦИЯМИ подстрок, а не целым
    блоком разметки: разметка миниатюры может измениться, порядок — нет.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(3)]
    ad_id = (await _seed_ad(db_session, title="Три вложения", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Три вложения", text="Текст", images=keys),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text
    # index() поднимает ValueError на отсутствующем ключе: «показаны все три» и
    # «показаны в этом порядке» проверяются одним выражением.
    positions = [html.index(key) for key in keys]
    assert positions == sorted(positions), "порядок миниатюр разошёлся с Ad.images"
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == keys


@pytest.mark.asyncio
async def test_removing_an_absent_key_changes_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-05: повторное «убрать вложение» на уже убранный ключ — без эффекта.

    Кнопка убирания живёт в форме автосохранения, и повторная отправка того же
    тела реальна: дебаунс мог отправить запрос дважды. Отбрасывание «лишнего»
    ключа или ошибка здесь одинаково испортили бы список.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(2)]
    absent = image_key(owner_id, "already-gone.jpg")
    ad_id = (await _seed_ad(db_session, title="Два вложения", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Два вложения",
            text="Текст",
            images=keys,
            extra=[("remove_image", absent)],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == keys


@pytest.mark.asyncio
async def test_remove_image_drops_one_key_and_keeps_order(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-05, D-12: убирание вложения снимает ровно один ключ и держит порядок.

    Именованная кнопка отправки — путь БЕЗ Alpine: она обязана работать сама по
    себе, иначе без скрипта вложение убрать нечем.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(3)]
    ad_id = (await _seed_ad(db_session, title="Три вложения", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Три вложения",
            text="Текст",
            images=keys,
            extra=[("remove_image", keys[1])],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == [keys[0], keys[2]]


@pytest.mark.asyncio
async def test_foreign_ad_is_not_autosavable(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02-21: чужое объявление недоступно на автосохранение.

    Владение проверяется внутри запроса, а не последующим `if`, поэтому «нет
    такой записи» и «запись чужая» дают один исход.
    """
    owner_id = (await _user(db_session)).id
    foreign = await _seed_ad(
        db_session, title="Чужое объявление", user_id=owner_id + 1000
    )
    foreign_id = foreign.id

    response = await authed_client.post(
        f"/ads/{foreign_id}/edit",
        content=form_body(title="Захват", text="Захват"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code != 200
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Ad).where(Ad.id == foreign_id))
    ).scalar_one()
    assert stored.title == "Чужое объявление"


# --- План 02-10, WR-03: файловая часть в поле вложений -----------------------


@pytest.mark.asyncio
async def test_multipart_file_part_in_images_is_refused(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Файловая часть в поле `images` — отказ по данным, а не ошибка 500.

    Чтение списка ключей вызывает строковую операцию у каждого значения
    `form_data.getlist("images")`. Многочастный запрос, в котором поле `images`
    приходит ФАЙЛОВОЙ частью, даёт объект загруженного файла, у которого такой
    операции нет, — и общий обработчик `app/main.py` превращает `AttributeError`
    в 500. Соседняя вспомогательная функция того же слоя уже защищается от
    этого класса ввода; защита приводится к единому виду.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, "p0.jpg")]
    ad_id = (await _seed_ad(db_session, title="С вложением", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        data={"title": "С вложением", "text": "Текст"},
        files={"images": ("payload.bin", b"\x00\x01\x02", "application/octet-stream")},
        follow_redirects=False,
    )

    assert response.status_code == 400
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == keys


# --- План 02-10: стражи, красной фазы не имеющие -----------------------------
#
# Три теста ниже воспроизведением дефекта НЕ являются и за него не выдаются.
#
# Контракт провода поля `status` закрепляет поведение, которое переименование
# параметра с алиасом по построению не меняет: тест зелен и до правки, и после,
# красным он не станет ни при каком порядке написания. Граница лимита вложений и
# порог счётчика закрепляют поведение, на текущем коде уже верное; они
# дописываются потому, что фаза их не закрепила, а не потому, что что-то сломано.


@pytest.mark.asyncio
async def test_status_field_keeps_its_wire_name(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Переименование параметра не меняет контракт провода (WR-08).

    Поле продолжает приходить под именем `status` и меняет состояние объявления
    только на значение из словаря состояний. Приняв тело с произвольной строкой,
    обработчик записал бы состояние, которое не отфильтровалось бы ни как
    черновик, ни как опубликованное.
    """
    owner_id = (await _user(db_session)).id
    ad_id = (await _seed_ad(db_session, title="Состояние с провода")).id

    known = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Состояние с провода",
            text="Текст",
            extra=[("status", AD_STATUS_PUBLISHED)],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert known.status_code == 302
    assert (await _only_ad(db_session, owner_id)).status == AD_STATUS_PUBLISHED

    unknown = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Состояние с провода", text="Текст", extra=[("status", "смешное")]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert unknown.status_code == 302
    assert (await _only_ad(db_session, owner_id)).status == AD_STATUS_PUBLISHED


@pytest.mark.asyncio
async def test_attachment_limit_is_a_closed_boundary(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """ADS-05: ровно лимит проходит, лимит плюс один — отказ без изменений.

    Значение берётся из настроек, а не из литерала: захардкоженная десятка
    прошла бы мимо смысла проверки при любой другой конфигурации.
    """
    limit = test_settings.max_images_per_ad
    owner_id = (await _user(db_session)).id
    exactly = [image_key(owner_id, f"p{i}.jpg") for i in range(limit)]
    ad_id = (await _seed_ad(db_session, title="Граница лимита")).id

    at_limit = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Граница лимита", text="Текст", images=exactly),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert at_limit.status_code == 302
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == exactly

    over = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Через границу",
            text="Текст",
            images=exactly + [image_key(owner_id, "one-too-many.jpg")],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert over.status_code == 400
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == exactly
    assert stored.title == "Граница лимита"


@pytest.mark.asyncio
async def test_counter_threshold_follows_the_presence_of_attachments(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E1 `overflow`: порог предупреждения выбирается по вложениям.

    С вложениями текст уходит ПОДПИСЬЮ К МЕДИА, и его предел существенно ниже
    (1024 против 4096). Один порог на оба случая либо пугал бы там, где всё в
    порядке, либо молчал бы перед гарантированной MediaCaptionTooLongError.

    Порог проверяется через разметку, где его видит пользователь: класс
    предупреждения на счётчике. Текст длиной 1500 символов лежит МЕЖДУ двумя
    порогами — выше `CAPTION_LIMIT` (1024) и ниже девяти десятых `TEXT_LIMIT`
    (3686), поэтому одно и то же значение обязано предупреждать при вложениях и
    молчать без них.
    """
    owner_id = (await _user(db_session)).id
    between = "я" * 1500
    assert CAPTION_LIMIT < len(between) < int(TEXT_LIMIT * TEXT_WARN_RATIO)

    with_images = await _seed_ad(
        db_session, title="С вложением", images=[image_key(owner_id, "p0.jpg")]
    )
    with_images_id = with_images.id
    without_images_id = (
        await _seed_ad(db_session, title="Без вложений", images=[])
    ).id

    # Текст в базу — тем же путём, которым его туда кладёт пользователь.
    for ad_id, images in ((with_images_id, [image_key(owner_id, "p0.jpg")]), (without_images_id, [])):
        saved = await authed_client.post(
            f"/ads/{ad_id}/edit",
            content=form_body(title="Длинный текст", text=between, images=images),
            headers=FORM_HEADERS,
            follow_redirects=False,
        )
        # Ни один порог не блокирует сохранение и не обрезает текст.
        assert saved.status_code == 302
        db_session.expire_all()
        stored = (
            await db_session.execute(select(Ad).where(Ad.id == ad_id))
        ).scalar_one()
        assert len(stored.text) == len(between), "текст обрезан на сохранении"

    warned = (await authed_client.get(f"/ads/{with_images_id}/edit")).text
    silent = (await authed_client.get(f"/ads/{without_images_id}/edit")).text

    assert "counter--warn" in _counter_class(warned), (
        "порог подписи к медиа не применён"
    )
    assert "counter--over" not in _counter_class(warned), (
        "предел текста не превышен — состояние «over» неверно"
    )
    assert "counter--warn" not in _counter_class(silent), (
        "без вложений порог должен быть выше — предупреждать нечему"
    )
    assert "maxlength" not in warned, "счётчик не имеет права обрезать текст"


@pytest.mark.asyncio
async def test_explicit_save_publishes_autosave_does_not(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-04: публикует явное «Сохранить», а не эвристика «текст непустой».

    Отдельной кнопки публикации в макете нет, поэтому состояние различается по
    признаку явной отправки. Эвристика опубликовала бы объявление, которое
    пользователь только начал набирать.
    """
    owner_id = (await _user(db_session)).id

    await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик", text="Текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    ad_id = (await _only_ad(db_session, owner_id)).id
    assert (await _only_ad(db_session, owner_id)).status == AD_STATUS_DRAFT

    await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Черновик", text="Текст", extra=[("save", "1")]),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert (await _only_ad(db_session, owner_id)).status == AD_STATUS_PUBLISHED


# --- План 02-04, Задача 3: разметка редактора --------------------------------
#
# Утверждения на РЕНДЕР, а не на исходник шаблона: контракт с обработчиком и
# порядок чтения проверяются там, где их видит браузер. Проверки исходного
# текста живут в tests/test_templates/test_ads_form_security.py и говорят о
# другом — о СПОСОБЕ сборки клиентской разметки.


@pytest.mark.asyncio
async def test_editor_has_two_column_containers(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Редактор собран на сетке раздела 8, а не на своей вёрстке."""
    ad = await _seed_ad(db_session, title="Объявление с сеткой")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "data-editor" in html
    assert "data-editor-side" in html


@pytest.mark.asyncio
async def test_editor_form_carries_autosave_and_stays_a_real_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Автосохранение — УСИЛЕНИЕ поверх настоящей формы, а не замена ей.

    Потеря `method`/`action` не роняет страницу: она молча лишает пользователя
    без JavaScript единственного способа сохранить объявление (D-09).
    """
    ad = await _seed_ad(db_session, title="Объявление с автосохранением")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'id="ad-form"' in html
    assert 'method="post"' in html
    assert f'action="/ads/{ad.id}/edit"' in html
    assert f'hx-post="/ads/{ad.id}/edit"' in html
    assert "delay:2s" in html, "дебаунс автосохранения потерян"
    assert 'hx-sync="this:queue last"' in html, (
        "наложение встаёт в очередь — отмена выбрасывала ответ с идентификатором (CR-04)"
    )
    assert "this:replace" not in html, "стратегия отмены вернулась — CR-04"
    assert 'hx-swap="none"' in html, "форма стала целью подмены — каретка потеряется"


@pytest.mark.asyncio
async def test_editor_shows_only_add_tile_without_attachments(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """0 вложений — только плитка добавления, не пустая рамка (UI-SPEC E3)."""
    ad = await _seed_ad(db_session, title="Без вложений", images=[])

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "media-tile--add" in html
    # ⚠️ ОСНОВАНИЕ ПРАВЛЕНО ВМЕСТЕ С ПРЕДМЕТОМ (Фаза 12, план 12-03), И ПРЕЖНЯЯ
    # РЕДАКЦИЯ НАЗЫВАЕТСЯ: здесь стояло «именно РАЗМЕТКА: имя класса встречается
    # ещё и в узловой сборке плиток, которая живёт в этом же файле и никуда не
    # выносится». Узловой сборки больше нет, и в документе имя класса встречается
    # ровно один раз — в разметке, которую печатает сервер. Утверждение от этого
    # стало ПРЯМЫМ, а не слабее: плитки убирания при нуле вложений нет вовсе.
    assert 'class="media-tile__remove"' not in html


@pytest.mark.asyncio
async def test_editor_hides_add_tile_at_the_limit(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """На лимите плитка добавления скрыта — она удобство, а не точка принуждения."""
    owner_id = (await _user(db_session)).id
    keys = [
        image_key(owner_id, f"p{i}.jpg")
        for i in range(test_settings.max_images_per_ad)
    ]
    ad = await _seed_ad(db_session, title="Полный комплект", images=keys)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "media-tile--add" in html, "плитка добавления удалена, а не скрыта"
    assert "media-tile--add hidden" in html or "media-tile--add\" hidden" in html


def _add_tile_tag(html: str) -> str:
    """Открывающий тег плитки добавления — И ТОЛЬКО ОН (Фаза 12, план 12-11).

    ⚠️ СРЕЗ ТЕГА, А НЕ ПОИСК ПО ВСЕМУ ОТВЕТУ, И ЭТО НЕСУЩЕЕ ТРЕБОВАНИЕ.
    Признак скрытости встречается в документе и у ДРУГИХ элементов; утверждение
    «`hidden` в ответе нет» было бы про чужую разметку и краснело бы (или, хуже,
    зеленело) на предмете, которого не касается. Спрашивается РОВНО одно: несёт
    ли признак скрытости САМА плитка добавления.

    Разбор строкой — тот же приём, что применяют соседние помощники модуля.
    Отсутствие элемента поднимает ValueError: тест падает, а не молча меряет
    пустоту.
    """
    anchor = html.index('id="media-add-tile"')
    return html[html.rindex("<", 0, anchor) : html.index(">", anchor) + 1]


@pytest.mark.asyncio
async def test_a_removal_at_the_ceiling_brings_the_add_tile_back(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Убирание на потолке возвращает «+ ФАЙЛ» БЕЗ перезагрузки страницы.

    ⚠️ ПЛИТКА ПОТЕРЯЛА СВОЕГО ОБНОВИТЕЛЯ ВМЕСТЕ С ПЕРЕРИСОВКОЙ ПОЛОСЫ, И ЭТО
    СЛЕДСТВИЕ ЗАДАЧИ 1, А НЕ ПРЕДСУЩЕСТВУЮЩИЙ ДЕФЕКТ (план 12-11). Прежде
    ответ убирания подменял узел полосы ЦЕЛИКОМ — и плитка добавления, живущая
    в том же узле, приезжала заново вместе с ним. Теперь ответ уносит РОВНО
    убранную плитку и чужого не трогает; значит «+ ФАЙЛ» обязана приехать СВОИМ
    блоком, иначе на потолке она осталась бы скрытой навсегда: человек убрал
    вложение, место освободилось, а выбрать следующий файл нечем до перезагрузки
    страницы.

    Скрытость проверяется СРЕЗОМ ТЕГА — основание у помощника выше.
    """
    owner_id = (await _user(db_session)).id
    keys = [
        image_key(owner_id, f"p{index}.jpg")
        for index in range(test_settings.max_images_per_ad)
    ]
    ad = await _seed_ad(db_session, title="Полный комплект", images=keys)

    page = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    # Идентификатор спрашивается ОТДЕЛЬНЫМ утверждением и ДО среза тега:
    # помощник среза падает громко (ValueError), а громкое падение — не то же
    # самое, что названная причина. Читателю покраснения нужна причина.
    assert 'id="media-add-tile"' in page, (
        "страница печатает плитку добавления БЕЗ идентификатора: адресовать её "
        "отдельным блоком ответа нечем, и после убирания на потолке она "
        "осталась бы скрытой до перезагрузки"
    )
    assert "hidden" in _add_tile_tag(page), (
        f"на потолке страница печатает плитку добавления ВИДИМОЙ: "
        f"{_add_tile_tag(page)!r} — правило измеряло бы возврат того, что и не "
        "уходило"
    )

    response = await authed_client.post(
        f"/ads/{ad.id}/edit",
        content=form_body(
            title="Полный комплект",
            text="Текст",
            images=keys,
            extra=[("remove_image", keys[0])],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert 'id="media-add-tile"' in response.text, (
        "ответ убирания не принёс плитку добавления: место освободилось, а "
        "выбрать следующий файл человек сможет только перезагрузив страницу"
    )
    assert "hidden" not in _add_tile_tag(response.text), (
        f"плитка добавления приехала СКРЫТОЙ: {_add_tile_tag(response.text)!r} "
        "— она врёт о потолке, которого после убирания уже нет"
    )


@pytest.mark.asyncio
async def test_attachment_remove_is_a_named_submit_inside_the_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Путь убирания вложения переживает отсутствие Alpine и htmx.

    Кнопка `type="button"` вместо именованной кнопки отправки лишила бы
    пользователя без скрипта единственного способа убрать вложение.
    """
    owner_id = (await _user(db_session)).id
    ad = await _seed_ad(
        db_session, title="С вложением", images=[image_key(owner_id, "p0.jpg")]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'name="remove_image"' in html
    assert 'aria-label="Убрать вложение"' in html
    assert 'type="submit"' in html


@pytest.mark.asyncio
async def test_editor_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удаление объявления — настоящая форма, перехват навешен на неё саму."""
    ad = await _seed_ad(db_session, title="Удаляемое объявление")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert f'action="/ads/{ad.id}/delete"' in html
    assert f"modal-open-ad-del-{ad.id}" in html
    assert 'role="dialog"' in html


@pytest.mark.asyncio
async def test_editor_markup_order_is_the_reading_order(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На ≤900px колонки схлопываются и порядок разметки становится порядком чтения.

    Поэтому предпросмотр обязан стоять ПОСЛЕ составителя: иначе на телефоне
    пользователь читает результат раньше, чем видит, где его набирать.

    Позиции берутся по подписи РАЗДЕЛА (`card__title`), а не по слову: слово
    «Расписания» есть и в боковом меню шелла, которое стоит выше по разметке.
    """
    ad = await _seed_ad(db_session, title="Порядок разметки")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    content = html.index('card__title">Содержание<')
    schedules = html.index('card__title">Расписания<')
    preview = html.index('card__title">Предпросмотр<')

    assert content < schedules < preview


@pytest.mark.asyncio
async def test_editor_renders_preview_summary_and_indicator_anchors(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Якоря внеполосной подмены есть на первичной отрисовке.

    Без них ответ автосохранения приходит в никуда: страница остаётся живой, а
    предпросмотр молча перестаёт обновляться.
    """
    ad = await _seed_ad(db_session, title="Якоря подмены")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'id="ad-preview"' in html
    assert 'id="ad-summary"' in html
    assert 'id="autosave-indicator"' in html


@pytest.mark.asyncio
async def test_editor_schedules_section_is_outside_the_ad_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Секция расписаний — СОСЕД формы объявления, а не её содержимое.

    Вложенные формы браузер молча отбрасывает: в плане 02-05 кнопки карточек
    расписаний перестали бы работать и с JavaScript, и без него.
    """
    ad = await _seed_ad(db_session, title="Место под расписания")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    form_start = html.index('id="ad-form"')
    form_end = html.index("</form>", form_start)
    schedules = html.index('card__title">Расписания<')

    assert schedules > form_end, "секция расписаний оказалась внутри формы объявления"


@pytest.mark.asyncio
async def test_editor_counter_is_server_rendered(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Счётчик длины приходит с сервера и не блокирует сохранение."""
    ad = await _seed_ad(db_session, title="Счётчик")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'id="text-counter"' in html
    assert "4096" in html, "предел длины не отрисован"
    assert "maxlength" not in html, "счётчик не имеет права обрезать текст"
