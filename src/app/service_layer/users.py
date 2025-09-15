import abc
import uuid

from app.models import User, UserRole

from ..exceptions import DuplicateError, NotFoundError, ValidationError
from ..utils.auth import hash_password
from .aClasses import AService
from .uow import AUnitOfWork


class AUsersService(AService, abc.ABC):
    @abc.abstractmethod
    async def create_user(
        self,
        *,
        username: str,
        email: str,
        fullname: str | None,
        is_active: bool,
        role: UserRole,
        password: str,
    ) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_user(self, user_id: uuid.UUID) -> User:
        raise NotImplementedError


class UsersService(AUsersService):
    def __init__(self, uow: AUnitOfWork):
        self.uow = uow

    async def create_user(
        self,
        *,
        username: str,
        email: str,
        fullname: str | None,
        is_active: bool,
        role: UserRole,
        password: str,
    ) -> User:
        if not username.strip():
            raise ValidationError("Username must not be empty")
        if not password:
            raise ValidationError("Password must not be empty")
        async with self.uow as uow_ctx:
            existing = await uow_ctx.users.get_by_email(email)
        if existing is not None:
            raise DuplicateError("User with this email already exists")

        salt, hashed = hash_password(password)

        new_user = User(
            username=username.strip(),
            email=email,
            fullname=fullname,
            is_active=is_active,
            role=role,
            password_salt=salt,
            password_hash=hashed,
        )

        async with self.uow as uow_ctx:
            await uow_ctx.users.add(new_user)

        return new_user

    async def get_user(self, id: uuid.UUID) -> User:
        async with self.uow as uow_ctx:
            user = await uow_ctx.users.get(id)
        if user is None:
            raise NotFoundError(f"User with id={id} not found")
        return user
