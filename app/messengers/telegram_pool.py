import structlog

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = structlog.get_logger(__name__)


class TelegramPool:
    """Maintains persistent TelegramClient connections per account."""

    def __init__(self):
        self._clients: dict[int, TelegramClient] = {}

    async def _create_client(
        self, session_string: str, api_id: int, api_hash: str
    ) -> TelegramClient:
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()
        return client

    async def get(
        self,
        account_id: int,
        session_string: str,
        api_id: int,
        api_hash: str,
    ) -> TelegramClient:
        """Get or create a connected TelegramClient for the given account."""
        client = self._clients.get(account_id)

        if client and client.is_connected():
            return client

        # Reconnect or create new
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

        try:
            client = await self._create_client(session_string, api_id, api_hash)
        except Exception as e:
            logger.error("telegram_pool_connect_error", account_id=account_id, error=str(e), exc_info=True)
            raise

        self._clients[account_id] = client
        logger.info("telegram_pool_connected", account_id=account_id)
        return client

    async def disconnect_all(self):
        """Disconnect all clients. Call on worker shutdown."""
        for account_id, client in self._clients.items():
            try:
                await client.disconnect()
                logger.info("telegram_pool_disconnected", account_id=account_id)
            except Exception as e:
                logger.warning(
                    "telegram_pool_disconnect_error", account_id=account_id, error=str(e)
                )
        self._clients.clear()

    async def remove(self, account_id: int):
        """Remove and disconnect a single client."""
        client = self._clients.pop(account_id, None)
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
