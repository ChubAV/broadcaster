from app.models.ad import Ad
from app.repositories.base import BaseRepository


class AdRepository(BaseRepository[Ad]):
    def __init__(self, session):
        super().__init__(session, Ad)
