"""Полная переинвентаризация состава групп аккаунта: D-10, D-11, D-12.

Файл — спецификация `app/application/accounts/group_resync.py`, единственной
реализации логики синка. До этой фазы блок синка был скопирован в трёх местах
(страничный TG-обработчик и две Celery-таски) с посимвольными расхождениями,
поэтому тесты стоят на хелпере, а не на трёх вызывающих: расхождение WA- и
MAX-путей ловится здесь один раз, а не тремя почти одинаковыми наборами.

Ключевое утверждение файла — НЕ «новые группы добавились», а
`test_missing_group_is_marked_not_deleted` вместе с
`test_resync_does_not_touch_is_active`. Обе проверки закрывают прохибицию
D-11: синхронизация НЕ ДОЛЖНА удалять данные пользователя и НЕ ДОЛЖНА
перетирать его выбор. Группа, которую мессенджер больше не вернул, помечается
временем пропажи и остаётся в списке — удаление остаётся решением
пользователя, а выключенная группа после синка обязана остаться выключенной.
Разница видна только на второй проверке: реализация «удалить пропавшие» тоже
прошла бы тест на счётчики, но молча стёрла бы группы, временно не отданные
мессенджером при сбое на его стороне.

`test_foreign_group_with_same_external_id_untouched` закрывает T-03-06:
внешний идентификатор уникален внутри мессенджера, но не внутри нашей базы, и
выборка существующих групп обязана скоупиться и по аккаунту, и по владельцу.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.accounts.dto import GroupResyncResult
from app.application.accounts.group_resync import (
    EMPTY_RESPONSE_MESSAGE,
    MALFORMED_RESPONSE_MESSAGE,
    apply_group_resync,
    parse_sync_result,
    record_sync_failure,
)
from app.database import Base
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.user import User


class _Db:
    """Собственный движок: хелпер не коммитит, транзакцией правит тест."""

    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def __aenter__(self) -> AsyncSession:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.session = factory()
        return self.session

    async def __aexit__(self, *exc):
        await self.session.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()


async def _seed_account(
    session: AsyncSession, email: str = "resync@test.com", type_: str = "wa"
) -> MessengerAccount:
    user = User(email=email, password_hash="x", name="U")
    session.add(user)
    await session.commit()

    account = MessengerAccount(
        user_id=user.id, type=type_, credentials="cred", status="syncing"
    )
    session.add(account)
    await session.commit()
    return account


async def _add_group(
    session: AsyncSession,
    account: MessengerAccount,
    external_id: str,
    name: str,
    *,
    is_active: bool = True,
    missing_since: datetime | None = None,
) -> Group:
    group = Group(
        user_id=account.user_id,
        account_id=account.id,
        messenger_type=account.type,
        group_external_id=external_id,
        name=name,
        is_active=is_active,
        missing_since=missing_since,
    )
    session.add(group)
    await session.commit()
    return group


async def _groups(session: AsyncSession, account: MessengerAccount) -> list[Group]:
    result = await session.execute(
        select(Group)
        .where(Group.account_id == account.id)
        .order_by(Group.group_external_id)
    )
    return list(result.scalars().all())


def _fetched(*pairs: tuple[str, str]) -> list[dict]:
    """Ответ мессенджера в том же виде, что отдают get_groups/get_sync_status."""
    return [{"id": external_id, "name": name} for external_id, name in pairs]


THREE = _fetched(("g1", "One"), ("g2", "Two"), ("g3", "Three"))


@pytest.mark.asyncio
async def test_new_groups_are_created_enabled():
    """Пустая база + три пришедшие группы: created=3, все включены."""
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(
            session, account, THREE, messenger_type="wa"
        )
        await session.commit()

        assert isinstance(result, GroupResyncResult)
        assert (result.found, result.created, result.renamed, result.missing) == (
            3,
            3,
            0,
            0,
        )
        assert result.error is None
        groups = await _groups(session, account)
        assert [g.group_external_id for g in groups] == ["g1", "g2", "g3"]
        assert all(g.is_active is True for g in groups)
        assert all(g.missing_since is None for g in groups)


@pytest.mark.asyncio
async def test_renamed_group_updates_name():
    """Тот же external_id с другим именем: renamed=1, имя обновлено."""
    async with _Db() as session:
        account = await _seed_account(session)
        await _add_group(session, account, "g1", "Старое имя")

        result = await apply_group_resync(
            session, account, _fetched(("g1", "Новое имя")), messenger_type="wa"
        )
        await session.commit()

        assert (result.created, result.renamed, result.missing) == (0, 1, 0)
        groups = await _groups(session, account)
        assert len(groups) == 1
        assert groups[0].name == "Новое имя"


@pytest.mark.asyncio
async def test_unchanged_group_is_not_counted_as_renamed():
    """Тот же external_id с тем же именем: ни создания, ни переименования."""
    async with _Db() as session:
        account = await _seed_account(session)
        await _add_group(session, account, "g1", "Имя")

        result = await apply_group_resync(
            session, account, _fetched(("g1", "Имя")), messenger_type="wa"
        )
        await session.commit()

        assert (result.found, result.created, result.renamed, result.missing) == (
            1,
            0,
            0,
            0,
        )


@pytest.mark.asyncio
async def test_missing_group_is_marked_not_deleted():
    """Группа, не вернувшаяся из мессенджера, помечается и остаётся (D-11)."""
    async with _Db() as session:
        account = await _seed_account(session)
        await _add_group(session, account, "g1", "Останется")

        result = await apply_group_resync(
            session, account, _fetched(("g2", "Новая")), messenger_type="wa"
        )
        await session.commit()

        assert (result.created, result.missing) == (1, 1)
        groups = await _groups(session, account)
        assert [g.group_external_id for g in groups] == ["g1", "g2"]
        gone = groups[0]
        assert gone.missing_since is not None
        assert gone.name == "Останется"


@pytest.mark.asyncio
async def test_returned_group_loses_missing_mark():
    """Вернувшаяся группа теряет пометку: missing_since снимается в None."""
    async with _Db() as session:
        account = await _seed_account(session)
        await _add_group(
            session,
            account,
            "g1",
            "Имя",
            missing_since=datetime.now(timezone.utc) - timedelta(days=2),
        )

        result = await apply_group_resync(
            session, account, _fetched(("g1", "Имя")), messenger_type="wa"
        )
        await session.commit()

        assert result.missing == 0
        groups = await _groups(session, account)
        assert groups[0].missing_since is None


@pytest.mark.asyncio
async def test_resync_does_not_touch_is_active():
    """Выключенная группа остаётся выключенной — и придя, и не придя.

    Прохибиция D-11 в чистом виде: пользовательский выбор синхронизацией не
    перетирается. Обе ветки в одном тесте намеренно — расхождение между ними
    и есть тот дефект, который тест ловит.
    """
    async with _Db() as session:
        account = await _seed_account(session)
        await _add_group(session, account, "g1", "Пришла", is_active=False)
        await _add_group(session, account, "g2", "Не пришла", is_active=False)

        result = await apply_group_resync(
            session, account, _fetched(("g1", "Пришла")), messenger_type="wa"
        )
        await session.commit()

        assert result.missing == 1
        groups = await _groups(session, account)
        came, gone = groups[0], groups[1]
        assert came.is_active is False
        assert came.missing_since is None
        assert gone.is_active is False
        assert gone.missing_since is not None


@pytest.mark.asyncio
async def test_second_identical_resync_is_idempotent():
    """Повторный вызов с тем же ответом не создаёт дублей и не считает лишнего."""
    async with _Db() as session:
        account = await _seed_account(session)

        await apply_group_resync(session, account, THREE, messenger_type="wa")
        await session.commit()

        second = await apply_group_resync(
            session, account, THREE, messenger_type="wa"
        )
        await session.commit()

        assert (second.found, second.created, second.renamed, second.missing) == (
            3,
            0,
            0,
            0,
        )
        assert len(await _groups(session, account)) == 3


@pytest.mark.asyncio
async def test_empty_response_marks_nothing_and_deletes_none():
    """Пустой ответ при непустом составе НЕ ставит ни одной пометки.

    Прежняя редакция теста закрепляла обратное — «пустой ответ помечает ВСЕ
    группы», — и ровно это поведение делало сбой мессенджера неотличимым от
    исчезновения всех чатов: после одного отказа моста помеченным оказывался
    весь список аккаунта, и настоящая пропажа одной группы становилась в нём
    неразличима. Ответ, не содержащий НИ ОДНОЙ ранее известной группы, — с
    большей вероятностью сбой мессенджера, чем одномоментный выход
    пользователя из всех чатов, поэтому он не применяется, а называет причину.
    """
    async with _Db() as session:
        account = await _seed_account(session)
        await apply_group_resync(session, account, THREE, messenger_type="wa")
        await session.commit()
        synced_at = account.last_synced_at

        result = await apply_group_resync(session, account, [], messenger_type="wa")
        await session.commit()

        assert (result.found, result.created, result.renamed, result.missing) == (
            0,
            0,
            0,
            0,
        )
        assert result.error == EMPTY_RESPONSE_MESSAGE
        groups = await _groups(session, account)
        assert len(groups) == 3
        assert all(g.missing_since is None for g in groups), (
            "сбой мессенджера не имеет права выглядеть как исчезновение всех групп"
        )
        # Причина уходит на аккаунт той же формой, что и любая другая ошибка,
        # — плашка на экране групп рисуется красной, а не зелёной.
        assert parse_sync_result(account.last_sync_result)["error"] == (
            EMPTY_RESPONSE_MESSAGE
        )
        # Синхронизация не состоялась — время последнего синка не переставляется.
        assert account.last_synced_at == synced_at


@pytest.mark.asyncio
async def test_empty_response_on_empty_account_is_a_normal_zero_sync():
    """Предохранитель НЕ срабатывает, когда терять нечего.

    Аккаунт без групп + пустой ответ — это правдоподобная пара, а не признак
    сбоя: ошибочно объявив её отказом, экран показывал бы красную плашку
    новому аккаунту, у которого действительно нет ни одного чата.
    """
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(session, account, [], messenger_type="wa")
        await session.commit()

        assert result.error is None
        assert (result.found, result.created, result.missing) == (0, 0, 0)
        assert account.last_synced_at is not None


@pytest.mark.asyncio
async def test_allow_full_wipe_puts_the_decision_on_the_caller():
    """Снять предохранитель можно только явно — и тогда пометки ставятся.

    Ни один существующий вызывающий его не снимает; параметр закреплён тестом,
    чтобы будущий достоверный путь объявлял себя явно, а не получал
    разрушительное поведение по умолчанию.
    """
    async with _Db() as session:
        account = await _seed_account(session)
        await apply_group_resync(session, account, THREE, messenger_type="wa")
        await session.commit()

        result = await apply_group_resync(
            session, account, [], messenger_type="wa", allow_full_wipe=True
        )
        await session.commit()

        assert (result.missing, result.error) == (3, None)
        groups = await _groups(session, account)
        assert len(groups) == 3, "снятый предохранитель всё равно не удаляет строк"
        assert all(g.missing_since is not None for g in groups)


@pytest.mark.asyncio
async def test_object_instead_of_list_is_refused_not_crashed():
    """Мост отдал JSON-объект — это отказ синка, а не AttributeError.

    `response.json()` не валидируется, и на `{"error": "..."}` цикл шёл бы по
    СТРОКОВЫМ ключам, а `str.get` давал бы AttributeError — пятисотку через
    generic_error_handler вместо внятной плашки.
    """
    async with _Db() as session:
        account = await _seed_account(session)
        await _add_group(session, account, "g1", "Живая")

        result = await apply_group_resync(
            session, account, {"error": "boom"}, messenger_type="wa"
        )
        await session.commit()

        assert result.error == MALFORMED_RESPONSE_MESSAGE
        assert (result.found, result.created, result.missing) == (0, 0, 0)
        assert (await _groups(session, account))[0].missing_since is None
        assert account.last_synced_at is None


@pytest.mark.asyncio
async def test_scalar_items_are_skipped_without_losing_the_rest():
    """Мусорный ЭЛЕМЕНТ стоит пропуска одной группы, а не всего синка.

    Ошибся отдельный чат, а не мост, поэтому отказ целиком здесь был бы
    несоразмерен: остальные группы аккаунта обязаны доехать.
    """
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(
            session,
            account,
            [1, None, "g1", {"id": "g2", "name": "Настоящая"}, []],
            messenger_type="wa",
        )
        await session.commit()

        assert result.error is None
        assert (result.found, result.created) == (1, 1)
        assert [g.group_external_id for g in await _groups(session, account)] == ["g2"]


@pytest.mark.asyncio
async def test_overlong_name_is_trimmed_to_the_column():
    """ИМЯ обрезается по границе колонки (String(255)).

    Класс дефекта, который зелёная суита поймать не может: на SQLite длина не
    проверяется вовсе, а на PostgreSQL строка длиннее 255 роняет commit с
    DataError — то есть ломается только прод. Для имени обрезка — верная
    реакция: цена ошибки косметическая, и синк целого аккаунта из-за одного
    длинного названия падать не должен.
    """
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(
            session,
            account,
            [{"id": "g1", "name": "и" * 5000}],
            messenger_type="wa",
        )
        await session.commit()

        assert result.created == 1
        group = (await _groups(session, account))[0]
        assert len(group.name) == 255
        assert group.group_external_id == "g1"


@pytest.mark.asyncio
async def test_overlong_external_id_skips_the_group_instead_of_trimming_it():
    """КЛЮЧ МАРШРУТИЗАЦИИ не обрезается — группа пропускается целиком.

    Обрезанный `group_external_id` не «читается хуже», он не адресует ничего:
    он уходит в мессенджер при каждой отправке
    (`use_cases.send_message_once`: `group_id=group.group_external_id`).
    Обрезка создала бы строку-призрак — видимую, выбираемую в расписании и
    молча проваливающую каждую отправку. Пропуск одной группы честнее.

    Соседняя годная группа обязана уцелеть: мусорный ЭЛЕМЕНТ не роняет весь
    синк.
    """
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(
            session,
            account,
            [{"id": "i" * 5000, "name": "Слишком длинный ключ"}, {"id": "g2", "name": "Годная"}],
            messenger_type="wa",
        )
        await session.commit()

        assert result.error is None, "один негодный элемент не роняет весь синк"
        assert (result.found, result.created) == (1, 1)
        assert [g.group_external_id for g in await _groups(session, account)] == ["g2"]


@pytest.mark.asyncio
async def test_two_overlong_ids_sharing_a_prefix_do_not_collapse_into_one():
    """Обрезка схлопнула бы разные ключи в один и нарушила уникальность.

    Два разных длинных идентификатора с одинаковым 255-символьным префиксом
    после обрезки становились одной строкой и упирались в
    `uq_groups_account_external` — то есть роняли синк ВСЕГО аккаунта
    IntegrityError-ом. Пропуск таких элементов снимает и этот путь.
    """
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(
            session,
            account,
            [
                {"id": "i" * 300 + "-a", "name": "Первая"},
                {"id": "i" * 300 + "-b", "name": "Вторая"},
            ],
            messenger_type="wa",
        )
        await session.commit()

        assert (result.found, result.created) == (0, 0)
        assert await _groups(session, account) == []


@pytest.mark.asyncio
async def test_nameless_group_falls_back_to_the_id():
    """Пустое имя подменяется идентификатором.

    Идентификатор здесь ровно на границе колонки: он проходит, а значит и
    подставленное из него имя укладывается в свою колонку без обрезки.
    """
    async with _Db() as session:
        account = await _seed_account(session)

        await apply_group_resync(
            session, account, [{"id": "i" * 255, "name": ""}], messenger_type="wa"
        )
        await session.commit()

        group = (await _groups(session, account))[0]
        assert group.name == "i" * 255


@pytest.mark.asyncio
async def test_duplicate_ids_in_response_create_one_row():
    """Дубли одного external_id внутри ответа схлопываются в одну строку."""
    async with _Db() as session:
        account = await _seed_account(session)

        result = await apply_group_resync(
            session,
            account,
            _fetched(("g1", "Первое"), ("g1", "Второе")),
            messenger_type="wa",
        )
        await session.commit()

        assert result.created == 1
        groups = await _groups(session, account)
        assert len(groups) == 1


@pytest.mark.asyncio
async def test_manually_deleted_group_returns_as_new():
    """D-10: удалённая пользователем группа возвращается новой и включённой."""
    async with _Db() as session:
        account = await _seed_account(session)
        # Удаляемая группа несёт состояние, отличимое от состояния новой:
        # выключена и помечена пропавшей. Именно оно и служит уликой — вернись
        # старая строка, эти значения приехали бы вместе с ней.
        group = await _add_group(
            session,
            account,
            "g1",
            "Имя",
            is_active=False,
            missing_since=datetime.now(timezone.utc),
        )
        await session.delete(group)
        await session.commit()

        result = await apply_group_resync(
            session, account, _fetched(("g1", "Имя")), messenger_type="wa"
        )
        await session.commit()

        assert result.created == 1
        groups = await _groups(session, account)
        assert len(groups) == 1
        revived = groups[0]
        # Строка создана заново, со значениями по умолчанию (D-10): включена и
        # без пометки. Сравнение id уликой служить НЕ может — SQLite переиспользует
        # rowid удалённой строки, и равенство id говорило бы о движке, а не о нас.
        assert revived.is_active is True
        assert revived.missing_since is None
        assert result.renamed == 0


@pytest.mark.asyncio
async def test_foreign_group_with_same_external_id_untouched():
    """T-03-06: чужая группа с тем же external_id не обновляется и не считается."""
    async with _Db() as session:
        mine = await _seed_account(session, email="mine@test.com")
        theirs = await _seed_account(session, email="theirs@test.com")
        foreign = await _add_group(session, theirs, "g1", "Чужое имя")

        result = await apply_group_resync(
            session, mine, _fetched(("g1", "Моё имя")), messenger_type="wa"
        )
        await session.commit()

        # Для моего аккаунта это НОВАЯ группа, а не переименование чужой.
        assert (result.created, result.renamed, result.missing) == (1, 0, 0)
        assert len(await _groups(session, mine)) == 1
        foreign_now = (
            await session.execute(select(Group).where(Group.id == foreign.id))
        ).scalar_one()
        assert foreign_now.name == "Чужое имя"
        assert foreign_now.missing_since is None


@pytest.mark.asyncio
async def test_row_with_a_diverged_user_id_is_updated_not_inserted_again():
    """Скоуп поиска совпадает со скоупом `uq_groups_account_external`.

    Ограничение скоупится ТОЛЬКО `account_id`. Пока словарь существующих строк
    строился ещё и по `user_id`, строка с разошедшимся владельцем (миграция
    данных, ручная правка) в него не попадала: хелпер считал группу новой,
    вставлял вторую строку на ту же пару и упирался в ограничение — то есть
    защитное условие превращало безобидное расхождение в отказ синхронизации
    ВСЕГО аккаунта.
    """
    async with _Db() as session:
        account = await _seed_account(session)
        stray = await _add_group(session, account, "g1", "Старое имя")
        # Расхождение владельца ровно того вида, что оставляет ручная правка.
        stray.user_id = account.user_id + 1000
        await session.commit()

        result = await apply_group_resync(
            session, account, _fetched(("g1", "Новое имя")), messenger_type="wa"
        )
        await session.commit()

        assert (result.created, result.renamed) == (0, 1), (
            "строка с чужим user_id принята за новую — коммит упрётся в "
            "уникальное ограничение и уронит синк всего аккаунта"
        )
        rows = await _groups(session, account)
        assert len(rows) == 1
        assert rows[0].name == "Новое имя"


@pytest.mark.asyncio
async def test_result_is_written_onto_account():
    """D-12: время и результат синка сохраняются на аккаунте в разбираемом виде."""
    async with _Db() as session:
        account = await _seed_account(session)
        before = datetime.now(timezone.utc)

        await apply_group_resync(session, account, THREE, messenger_type="wa")
        await session.commit()

        assert account.last_synced_at is not None
        assert account.last_synced_at.tzinfo is not None
        assert account.last_synced_at >= before
        payload = json.loads(account.last_sync_result)
        assert payload == {
            "found": 3,
            "new": 3,
            "renamed": 0,
            "missing": 0,
            "error": None,
        }


@pytest.mark.asyncio
async def test_record_sync_failure_writes_error_with_zero_counters():
    """Ошибка синка пишется той же формой: счётчики нулевые, error — текст."""
    async with _Db() as session:
        account = await _seed_account(session)

        await record_sync_failure(session, account, "мессенджер не ответил")
        await session.commit()

        payload = json.loads(account.last_sync_result)
        assert payload == {
            "found": 0,
            "new": 0,
            "renamed": 0,
            "missing": 0,
            "error": "мессенджер не ответил",
        }


@pytest.mark.asyncio
async def test_record_sync_failure_does_not_move_last_synced_at():
    """Провал не переставляет `last_synced_at`: синхронизация не состоялась.

    Колонка означает «синк состоялся», и оба потребителя читают её так. Пока
    провал её переставлял, экран сообщал два противоречащих факта разом
    («последняя синхронизация только что» + красная плашка «не удалась»), а
    аккаунт, у которого синк не удавался НИ РАЗУ и групп никогда не было,
    получал пустое состояние «Все группы удалены».
    """
    async with _Db() as session:
        # Свежий аккаунт: синхронизации не было ни одной.
        account = await _seed_account(session)
        assert account.last_synced_at is None

        await record_sync_failure(session, account, "мост не ответил")
        await session.commit()

        assert account.last_synced_at is None

        # А удавшийся синк её ставит — иначе тест зеленел бы и на реализации,
        # которая не пишет колонку вовсе.
        await apply_group_resync(session, account, THREE, messenger_type="wa")
        await session.commit()
        succeeded_at = account.last_synced_at
        assert succeeded_at is not None

        # И следующий провал не сдвигает время последнего УДАВШЕГОСЯ синка.
        await record_sync_failure(session, account, "мост снова не ответил")
        await session.commit()
        assert account.last_synced_at == succeeded_at


@pytest.mark.asyncio
async def test_helper_does_not_commit():
    """Транзакцией правит вызывающий: страница и Celery-таска ведут её по-разному."""
    async with _Db() as session:
        account = await _seed_account(session)
        # id снимается ДО отката: откат обесценивает загруженные атрибуты, и
        # обращение к account.id после него полезло бы в базу за перезагрузкой.
        account_id = account.id

        await apply_group_resync(session, account, THREE, messenger_type="wa")

        assert session.in_transaction()
        await session.rollback()

        rows = await session.execute(
            select(Group).where(Group.account_id == account_id)
        )
        assert list(rows.scalars().all()) == []


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(None, id="none"),
        pytest.param("", id="empty"),
        pytest.param("{не json", id="broken-json"),
        pytest.param("[1, 2, 3]", id="not-a-dict"),
        pytest.param('"строка"', id="scalar"),
    ],
)
def test_parse_sync_result_degrades_to_none(raw):
    """Мусор в колонке даёт None, а не исключение.

    Плашка результата обязана деградировать в ОТСУТСТВИЕ плашки, а не в
    стек-трейс на экране групп (T-03-08): значение пишется только кодом, но
    пережить чужую запись и обрыв на полуслове обязано.
    """
    assert parse_sync_result(raw) is None


def test_parse_sync_result_reads_valid_payload():
    payload = '{"found": 5, "new": 2, "renamed": 1, "missing": 0, "error": null}'
    assert parse_sync_result(payload) == {
        "found": 5,
        "new": 2,
        "renamed": 1,
        "missing": 0,
        "error": None,
    }
