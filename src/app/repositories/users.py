import abc
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import ARepository


class AUsersRepository(ARepository[User, UUID], abc.ABC):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    @abc.abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError


class UsersRepository(AUsersRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(self.model_class).filter_by(email=email)
        result = await self.session.execute(stmt)
        user = result.scalars().one_or_none()
        return user
