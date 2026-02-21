from sqlalchemy import select

from app.models.messenger_account import MessengerAccount
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[MessengerAccount]):
    def __init__(self, session):
        super().__init__(session, MessengerAccount)

    async def get_by_type_and_status(
        self, user_id: int, account_type: str, status: str
    ) -> MessengerAccount | None:
        result = await self.session.execute(
            select(MessengerAccount).where(
                MessengerAccount.user_id == user_id,
                MessengerAccount.type == account_type,
                MessengerAccount.status == status,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_type_and_status(
        self, user_id: int, account_type: str, status: str
    ) -> list[MessengerAccount]:
        result = await self.session.execute(
            select(MessengerAccount).where(
                MessengerAccount.user_id == user_id,
                MessengerAccount.type == account_type,
                MessengerAccount.status == status,
            )
        )
        return list(result.scalars().all())
