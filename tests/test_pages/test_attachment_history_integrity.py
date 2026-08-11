"""Запрет фазы 02-04: удаление вложения НЕ разрушает историю отправленного.

Отдельный файл, а не дописка к `test_ads_editor.py`, — намеренно. Утверждение
принадлежит ЗАПРЕТУ фазы, а не регрессии редактора, и обязано быть находимым по
имени: отчёт верификации пометил запрет `⚠ FLAGGED — unverified enforcement`
ровно потому, что структурный довод был, а именованного теста не было — «ни
одной ссылки на `SendLog` в регрессии редактора».

Структурный довод сам по себе недостаточен. `SendLog.ad_images` — независимая
JSON-колонка снапшота (`app/models/send_log.py:21`), и правка `Ad.images` её не
касается; вызова удаления объекта в хранилище на пути `remove_image` нет вовсе.
Но «сегодня в исходнике нет вызова» — свойство ТЕКСТА, а не поведения: оно
перестаёт быть верным ровно в тот момент, когда кто-нибудь добавит уборку
осиротевших объектов, и грепом это не удержать. Здесь удерживается ПОВЕДЕНИЕМ.

Обе половины запрета:

* снапшот отправленного переживает удаление вложения из объявления
  (`test_send_log_snapshot_survives_attachment_removal`);
* объект в хранилище не удаляется, поэтому просмотр прошлой отправки не
  превращается в битую картинку
  (`test_removing_an_attachment_does_not_touch_storage`).
"""

from urllib.parse import urlencode
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.s3 as s3_module
from app.models.ad import Ad
from app.models.send_log import SendLog
from app.models.user import User

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

# Имена, по которым опознаётся функция удаления объекта хранилища. Сегодня в
# `app/services/s3.py` таких функций нет вовсе (модуль умеет только строить
# адрес и загружать), поэтому перечень ничего не находит — и это ожидаемо. Он
# существует для БУДУЩЕГО: появившаяся функция удаления будет обёрнута
# счётчиком автоматически, и тест поймает её вызов с пути убирания вложения.
DELETION_NAME_PARTS = ("delete", "remove", "purge", "destroy")


def image_key(user_id: int, name: str = "photo.jpg") -> str:
    """Ключ вложения в форме, которую выдаёт загрузка: `{user_id}/{32 hex}_{имя}`.

    Форма обязательна: `own_image_keys` (план 02-02, ужесточён планом 02-10)
    отклоняет всё остальное, и тест на произвольной строке померил бы отказ
    проверки владения, а не целость снапшота.
    """
    return f"{user_id}/{uuid4().hex}_{name}"


def form_body(title: str, text: str, images: list[str], removed: str) -> str:
    fields: list[tuple[str, str]] = [("title", title), ("text", text)]
    fields += [("images", value) for value in images]
    fields.append(("remove_image", removed))
    return urlencode(fields)


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(db: AsyncSession, user_id: int, images: list[str]) -> int:
    """Объявление с вложениями. Возвращает ИДЕНТИФИКАТОР, а не живой объект.

    Дальше по тесту будут ещё коммиты, а они сбрасывают загруженные атрибуты:
    обращение к `ad.id` после чужого коммита уходило бы в ленивую подгрузку вне
    greenlet-а и роняло тест инфраструктурной причиной вместо содержательной
    (тот же дефект встречался в планах 02-08 и 02-10).
    """
    ad = Ad(
        user_id=user_id,
        title="Объявление с историей отправок",
        text="Текст объявления на момент отправки",
        images=list(images),
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad.id


async def _seed_send_log(
    db: AsyncSession, user_id: int, ad_id: int, images: list[str], text: str
) -> int:
    """Строка истории со СНАПШОТОМ отправленного.

    Снапшот — не ссылка на объявление, а его копия на момент отправки: именно
    поэтому история обязана пережить любую последующую правку объявления.
    """
    log = SendLog(
        user_id=user_id,
        schedule_id=None,
        ad_id=ad_id,
        group_id=None,
        ad_title="Объявление с историей отправок",
        ad_text=text,
        ad_images=list(images),
        group_name="Барахолка Северного района",
        messenger_type="wa",
        status="success",
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log.id


# --- Счётчик обращений к хранилищу -------------------------------------------
#
# План предписывал подменить «соответствующий вызов в app/services/s3.py» на
# объект-счётчик. Функции удаления в этом модуле НЕ СУЩЕСТВУЕТ — он умеет ровно
# `get_image_url` и `upload_file_to_s3`, — поэтому подменяется то, через что
# любое удаление неизбежно прошло бы: фабрика клиента хранилища. Счётчик стоит
# на ГРАНИЦЕ, а не на конкретном имени, и поэтому переживёт появление функции
# удаления вместо того, чтобы молча пропустить её мимо.


class _RecordingClient:
    """Клиент хранилища, который ничего не делает и всё записывает."""

    def __init__(self, calls: list[str]):
        self._calls = calls

    def __getattr__(self, name: str):
        async def _record(*args, **kwargs):
            self._calls.append(f"client.{name}")
            return {}

        return _record


class _ClientContext:
    def __init__(self, calls: list[str]):
        self._calls = calls

    async def __aenter__(self) -> _RecordingClient:
        return _RecordingClient(self._calls)

    async def __aexit__(self, *exc_info) -> bool:
        return False


class _RecordingSession:
    def __init__(self, calls: list[str]):
        self._calls = calls

    def create_client(self, **kwargs) -> _ClientContext:
        self._calls.append(f"create_client:{kwargs.get('service_name')}")
        return _ClientContext(self._calls)


@pytest.fixture
def storage_calls(monkeypatch) -> list[str]:
    """Журнал ВСЕХ обращений к объектному хранилищу за время теста.

    Записываются две вещи: создание клиента хранилища (единственная дверь, за
    которой живут `put_object`, `delete_object` и всё остальное) и вызов любой
    функции модуля, чьё имя говорит об удалении.
    """
    calls: list[str] = []

    monkeypatch.setattr(
        s3_module, "AioSession", lambda *args, **kwargs: _RecordingSession(calls)
    )

    for name in dir(s3_module):
        if name.startswith("_"):
            continue
        attr = getattr(s3_module, name)
        if not callable(attr):
            continue
        if not any(part in name.lower() for part in DELETION_NAME_PARTS):
            continue

        def _wrap(original, label):
            def _counting(*args, **kwargs):
                calls.append(f"s3.{label}")
                return original(*args, **kwargs)

            return _counting

        monkeypatch.setattr(s3_module, name, _wrap(attr, name))

    return calls


@pytest.mark.asyncio
async def test_send_log_snapshot_survives_attachment_removal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Убирание вложения из объявления не трогает снапшот отправленного.

    Список ключей ОБЪЯВЛЕНИЯ становится короче на один — это и есть смысл
    действия. Список ключей СНАПШОТА не меняется ни по составу, ни по порядку:
    порядок ключей — это порядок отправки, и переставленный снапшот показал бы
    историю, которой не было. Текст снапшота тоже остаётся прежним, хотя тот же
    запрос меняет текст объявления.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(2)]
    sent_text = "Текст объявления на момент отправки"
    ad_id = await _seed_ad(db_session, owner_id, keys)
    log_id = await _seed_send_log(db_session, owner_id, ad_id, keys, sent_text)

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Объявление с историей отправок",
            text="Текст объявления ПОСЛЕ правки",
            images=keys,
            removed=keys[0],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302

    db_session.expire_all()
    ad = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    log = (
        await db_session.execute(select(SendLog).where(SendLog.id == log_id))
    ).scalar_one()

    assert ad.images == [keys[1]], "убирание сняло не ровно один ключ объявления"
    assert log.ad_images == keys, (
        "снапшот отправленного изменился вслед за правкой объявления — "
        "история отправок переписана задним числом"
    )
    assert log.ad_text == sent_text, "текст снапшота уехал за текстом объявления"


@pytest.mark.asyncio
async def test_removing_an_attachment_does_not_touch_storage(
    authed_client: AsyncClient, db_session: AsyncSession, storage_calls: list[str]
):
    """Путь убирания вложения не удаляет объект в хранилище (D-12).

    Ключ, убранный из объявления, остаётся в снапшоте отправки, и снапшот
    ссылается на ТОТ ЖЕ объект. Удали его уборщик осиротевших ключей — просмотр
    прошлой отправки превратился бы в битую картинку, а сама отправка стала бы
    недоказуемой.

    Утверждение ведётся счётчиком обращений к хранилищу, а не грепом по
    исходнику: греп проверяет текст сегодняшнего кода, счётчик — поведение
    любого будущего.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(2)]
    ad_id = await _seed_ad(db_session, owner_id, keys)
    await _seed_send_log(
        db_session, owner_id, ad_id, keys, "Текст объявления на момент отправки"
    )

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Объявление с историей отправок",
            text="Текст объявления на момент отправки",
            images=keys,
            removed=keys[0],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert storage_calls == [], (
        f"путь убирания вложения обратился к хранилищу: {storage_calls}"
    )


@pytest.mark.asyncio
async def test_storage_counter_observes_the_boundary_it_claims_to_watch(
    storage_calls: list[str],
):
    """Парный тест: без него предыдущий зеленел бы на неустановленном счётчике.

    «Ноль вызовов» — утверждение о ПУСТОТЕ, и оно неотличимо от «счётчик
    подменил не то, что вызывается». Тот же класс вакуумной проверки уже
    ловился в плане 02-10 (порог счётчика по всей странице). Здесь граница
    дёргается напрямую: если подмена промахнулась мимо фабрики клиента, журнал
    останется пустым и ЭТОТ тест упадёт первым.
    """
    await s3_module.upload_file_to_s3(
        content=b"\x89PNG",
        key="1/deadbeef_probe.png",
        content_type="image/png",
        endpoint_url="https://storage.invalid",
        access_key="k",
        secret_key="s",
        bucket="bucket",
    )

    assert storage_calls == ["create_client:s3", "client.put_object"]
