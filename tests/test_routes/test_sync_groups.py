import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.group import Group
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def sync_setup():
    """Full setup with db session factory for sync-groups tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
    )
    app = create_app(settings=settings)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as client:
        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _login(client: AsyncClient) -> None:
    """Register and login via API + page forms, storing cookie on the client."""
    await client.post("/api/auth/register", json={
        "email": "sync@test.com", "password": "pass123", "name": "Sync User",
    })
    await client.post("/login", data={"email": "sync@test.com", "password": "pass123"})


async def _make_account(session_factory, *, email: str = "sync@test.com",
                        type_: str = "tg_user", status: str = "active") -> int:
    """Создаёт аккаунт указанного пользователя и возвращает его id."""
    from app.models.user import User

    async with session_factory() as session:
        user = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type=type_,
            credentials="session-string",
            status=status,
        )
        session.add(account)
        await session.commit()
        return account.id


async def _add_group(session_factory, account_id: int, external_id: str, name: str,
                     *, is_active: bool = True) -> int:
    """Кладёт группу в базу от имени владельца аккаунта."""
    async with session_factory() as session:
        account = await session.get(MessengerAccount, account_id)
        group = Group(
            user_id=account.user_id,
            account_id=account_id,
            messenger_type=account.type,
            group_external_id=external_id,
            name=name,
            is_active=is_active,
        )
        session.add(group)
        await session.commit()
        return group.id


async def _account_result(session_factory, account_id: int):
    """Возвращает (last_synced_at, разобранный last_sync_result) аккаунта."""
    from app.application.accounts.group_resync import parse_sync_result

    async with session_factory() as session:
        account = await session.get(MessengerAccount, account_id)
        return account.last_synced_at, parse_sync_result(account.last_sync_result)


@pytest.mark.asyncio
async def test_sync_groups_creates_groups(sync_setup):
    client, session_factory = sync_setup
    await _login(client)

    # Create tg_user account directly in DB
    async with session_factory() as session:
        # Find user
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session-string",
            status="active",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    # Mock TelegramUserMessenger.get_groups
    mock_groups = [
        {"id": "-100111", "name": "Group A"},
        {"id": "-100222", "name": "Group B"},
    ]

    with patch(
        "app.pages.accounts.TelegramUserMessenger"
    ) as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_groups = AsyncMock(return_value=mock_groups)

        resp = await client.post(f"/accounts/{account_id}/sync-groups")

    assert resp.status_code == 200  # followed redirect to /groups

    async with session_factory() as session:
        result = await session.execute(
            select(Group).where(Group.account_id == account_id).order_by(Group.id)
        )
        groups = result.scalars().all()
        assert len(groups) == 2
        assert groups[0].name == "Group A"
        assert groups[0].group_external_id == "-100111"
        assert groups[1].name == "Group B"
        assert groups[1].group_external_id == "-100222"


@pytest.mark.asyncio
async def test_sync_groups_uses_settings_api_credentials(sync_setup):
    """Verify that sync_groups passes api_id/api_hash from settings to TelegramUserMessenger."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session-string",
            status="active",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch(
        "app.pages.accounts.TelegramUserMessenger"
    ) as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_groups = AsyncMock(return_value=[])

        await client.post(f"/accounts/{account_id}/sync-groups")

        MockMessenger.assert_called_once_with(
            session_string="session-string",
            api_id=12345,
            api_hash="test_api_hash",
        )


@pytest.mark.asyncio
async def test_sync_groups_always_uses_settings_credentials(sync_setup):
    """Sync groups always uses api_id/api_hash from settings, even when zero."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    # Settings with no telegram_api_id
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=0,
        telegram_api_hash="",
    )
    app = create_app(settings=settings)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as client:
        await client.post("/api/auth/register", json={
            "email": "fallback@test.com", "password": "pass123", "name": "Fallback User",
        })
        await client.post("/login", data={"email": "fallback@test.com", "password": "pass123"})

        async with session_factory() as session:
            from app.models.user import User

            user = (await session.execute(select(User))).scalar_one()
            account = MessengerAccount(
                user_id=user.id,
                type="tg_user",
                credentials="session-string",
                status="active",
            )
            session.add(account)
            await session.commit()
            account_id = account.id

        with patch(
            "app.pages.accounts.TelegramUserMessenger"
        ) as MockMessenger:
            instance = MockMessenger.return_value
            instance.get_groups = AsyncMock(return_value=[])

            await client.post(f"/accounts/{account_id}/sync-groups")

            MockMessenger.assert_called_once_with(
                session_string="session-string",
                api_id=0,
                api_hash="",
            )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_sync_groups_skips_existing(sync_setup):
    client, session_factory = sync_setup
    await _login(client)

    # Create tg_user account and one existing group
    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session-string",
            status="active",
        )
        session.add(account)
        await session.flush()

        existing_group = Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type="tg_user",
            group_external_id="-100111",
            name="Existing Group A",
        )
        session.add(existing_group)
        await session.commit()
        account_id = account.id

    mock_groups = [
        {"id": "-100111", "name": "Group A (updated name)"},
        {"id": "-100333", "name": "Group C"},
    ]

    with patch(
        "app.pages.accounts.TelegramUserMessenger"
    ) as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_groups = AsyncMock(return_value=mock_groups)

        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        result = await session.execute(
            select(Group).where(Group.account_id == account_id).order_by(Group.id)
        )
        groups = result.scalars().all()
        # Should have 2: existing + new, no duplicate
        assert len(groups) == 2
        # D-11: имя существующей группы обновляется ответом мессенджера,
        # второй строки при этом не появляется
        assert groups[0].name == "Group A (updated name)"
        assert groups[0].group_external_id == "-100111"
        # New group created
        assert groups[1].name == "Group C"
        assert groups[1].group_external_id == "-100333"


# --- План 03-04: TG-синк через общий хелпер, результат на аккаунте (D-09…D-12) ---


@pytest.mark.asyncio
async def test_sync_records_result_on_account(sync_setup):
    """После успешного синка на аккаунте есть время синка и разбираемая сводка."""
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)

    mock_groups = [
        {"id": "-1", "name": "Один"},
        {"id": "-2", "name": "Два"},
        {"id": "-3", "name": "Три"},
    ]

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(return_value=mock_groups)
        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        groups = (
            await session.execute(select(Group).where(Group.account_id == account_id))
        ).scalars().all()
        assert len(groups) == 3

    last_synced_at, result = await _account_result(session_factory, account_id)
    assert last_synced_at is not None
    assert result is not None
    assert result["found"] == 3
    assert result["new"] == 3
    assert result["renamed"] == 0
    assert result["missing"] == 0
    assert result["error"] is None


@pytest.mark.asyncio
async def test_sync_renames_existing_group(sync_setup):
    """D-11: изменившееся в мессенджере имя доезжает до строки и считается."""
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)
    group_id = await _add_group(session_factory, account_id, "-1", "Старое имя")

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(
            return_value=[{"id": "-1", "name": "Новое имя"}]
        )
        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        group = await session.get(Group, group_id)
        assert group.name == "Новое имя"

    _, result = await _account_result(session_factory, account_id)
    assert result["renamed"] == 1
    assert result["new"] == 0


@pytest.mark.asyncio
async def test_sync_marks_missing_group_but_keeps_it(sync_setup):
    """D-11: не вернувшаяся группа помечается, но остаётся в базе.

    Ответ содержит ДРУГУЮ группу, а не пуст: пустой ответ при непустом составе
    отклоняется предохранителем `apply_group_resync` как вырожденный, и на нём
    эта проверка проходила бы по совсем другой ветке.
    """
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)
    group_id = await _add_group(session_factory, account_id, "-1", "Пропавшая")

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(
            return_value=[{"id": "-2", "name": "Оставшаяся"}]
        )
        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        group = await session.get(Group, group_id)
        assert group is not None, "синк не имеет права удалять группы пользователя"
        assert group.missing_since is not None

    _, result = await _account_result(session_factory, account_id)
    assert result["missing"] == 1


@pytest.mark.asyncio
async def test_sync_refuses_to_mark_everything_on_an_empty_response(sync_setup):
    """Пустой ответ при непустом составе не помечает НИ ОДНОЙ группы.

    Достижимо независимо от отказа адаптера: WA/MAX-мост при `state == "ready"`
    вправе положить в `groups` `null` или `[]`, а разлогиненная сессия отдаёт
    200 с пустым списком. Зелёная сводка «не найдено 42» на таком ответе
    обесценивала признак «не найдена при синке» целиком.
    """
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)
    first = await _add_group(session_factory, account_id, "-1", "Первая")
    second = await _add_group(session_factory, account_id, "-2", "Вторая")

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(return_value=[])
        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        for group_id in (first, second):
            group = await session.get(Group, group_id)
            assert group.missing_since is None

    _, result = await _account_result(session_factory, account_id)
    assert result["missing"] == 0
    assert result["error"], "вырожденный ответ обязан объяснить себя пользователю"


@pytest.mark.asyncio
async def test_sync_keeps_disabled_group_disabled(sync_setup):
    """D-11: включённость — выбор пользователя, синк её не переписывает."""
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)
    group_id = await _add_group(
        session_factory, account_id, "-1", "Выключенная", is_active=False
    )

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(
            return_value=[{"id": "-1", "name": "Выключенная"}]
        )
        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        group = await session.get(Group, group_id)
        assert group.is_active is False

    # Сводка обязана подтвердить, что группа была УВИДЕНА синком: иначе тест
    # зеленел бы и на пути, который до неё просто не дошёл.
    _, result = await _account_result(session_factory, account_id)
    assert result["found"] == 1
    assert result["new"] == 0


@pytest.mark.asyncio
async def test_sync_redirects_to_account_groups_screen(sync_setup):
    """Пользователь возвращается на экран групп ТОГО аккаунта, с которым работал."""
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(return_value=[])
        resp = await client.post(
            f"/accounts/{account_id}/sync-groups", follow_redirects=False
        )

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/accounts/{account_id}/groups"


@pytest.mark.asyncio
async def test_sync_while_syncing_does_not_touch_messenger(sync_setup):
    """Guard повторного запуска: второй запрос не идёт в мессенджер."""
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory, status="syncing")

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        resp = await client.post(
            f"/accounts/{account_id}/sync-groups", follow_redirects=False
        )

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/accounts/{account_id}/groups"
    MockMessenger.assert_not_called()

    last_synced_at, result = await _account_result(session_factory, account_id)
    assert last_synced_at is None
    assert result is None


@pytest.mark.asyncio
async def test_sync_foreign_account_changes_nothing(sync_setup):
    """T-03-14: чужой account_id не запускает синк и не меняет состояния."""
    client, session_factory = sync_setup
    await _login(client)

    await client.post("/api/auth/register", json={
        "email": "other@test.com", "password": "pass123", "name": "Other User",
    })
    foreign_id = await _make_account(session_factory, email="other@test.com")

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        resp = await client.post(
            f"/accounts/{foreign_id}/sync-groups", follow_redirects=False
        )

    assert resp.status_code == 302
    assert resp.headers["location"] == "/accounts"
    MockMessenger.assert_not_called()

    last_synced_at, result = await _account_result(session_factory, foreign_id)
    assert last_synced_at is None
    assert result is None
    async with session_factory() as session:
        groups = (
            await session.execute(select(Group).where(Group.account_id == foreign_id))
        ).scalars().all()
        assert groups == []


@pytest.mark.asyncio
async def test_sync_failure_is_recorded_not_swallowed(sync_setup):
    """Отказ мессенджера записывается на аккаунт, а не теряется."""
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory)

    with patch("app.pages.accounts.TelegramUserMessenger") as MockMessenger:
        MockMessenger.return_value.get_groups = AsyncMock(
            side_effect=RuntimeError("сессия Telegram протухла")
        )
        resp = await client.post(
            f"/accounts/{account_id}/sync-groups", follow_redirects=False
        )

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/accounts/{account_id}/groups"

    last_synced_at, result = await _account_result(session_factory, account_id)
    assert last_synced_at is not None
    assert result is not None
    assert "сессия Telegram протухла" in result["error"]


@pytest.mark.asyncio
async def test_bridge_failure_reaches_the_account_through_the_real_adapter(sync_setup):
    """Отказ моста доезжает до сводки через НАСТОЯЩИЙ класс адаптера.

    Соседний test_sync_failure_is_recorded_not_swallowed подменяет сам метод
    `get_groups` моком с side_effect — то есть проверяет контракт, которого у
    настоящего класса могло и не быть: пока адаптеры глушили исключение и
    возвращали `[]`, тест зеленел, а прод молча помечал пропавшими все группы
    аккаунта. Здесь подменён только HTTP-слой, а `WhatsAppMessenger` — живой,
    поэтому тест падает ровно тогда, когда контракт адаптера ломается.
    """
    client, session_factory = sync_setup
    await _login(client)
    account_id = await _make_account(session_factory, type_="wa")
    group_id = await _add_group(session_factory, account_id, "-1@g.us", "Живая")

    mock_response = MagicMock()
    mock_response.status_code = 502

    with patch("app.messengers.whatsapp.ensure_wa_container", return_value="http://fake:3000"), \
         patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        resp = await client.post(
            f"/accounts/{account_id}/sync-groups", follow_redirects=False
        )

    assert resp.status_code == 302

    _, result = await _account_result(session_factory, account_id)
    assert result is not None
    assert result["error"], "отказ моста обязан лечь на аккаунт ошибкой, а не сводкой успеха"
    assert "502" in result["error"]

    # И главное следствие: ни одна группа не помечена пропавшей.
    async with session_factory() as session:
        group = await session.get(Group, group_id)
        assert group.missing_since is None, (
            "сбой моста не имеет права выглядеть как исчезновение групп"
        )


