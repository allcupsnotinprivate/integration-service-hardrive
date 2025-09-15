import abc
import asyncio
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.models import User

from ..exceptions import exceptions
from ..utils.auth import verify_password
from .aClasses import AService
from .uow import AUnitOfWork


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str


@dataclass(slots=True)
class _TokenRecord:
    user_id: uuid.UUID
    expires_at: datetime


class A_AuthService(AService):
    @abc.abstractmethod
    async def authenticate(self, email: str, password: str) -> TokenPair:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_user_by_access_token(self, access_token: str) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    async def logout(self, access_token: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def refresh_tokens(self, access_token: str, refresh_token: str) -> TokenPair:
        raise NotImplementedError


class AuthService(A_AuthService):
    def __init__(self, access_ttl: int, refresh_ttl: int, uow: AUnitOfWork):
        # params
        self._access_ttl = timedelta(seconds=access_ttl)
        self._refresh_ttl = timedelta(seconds=refresh_ttl)
        self.uow = uow
        # resources
        self._lock = asyncio.Lock()
        self._access_tokens: dict[str, _TokenRecord] = {}
        self._refresh_tokens: dict[str, _TokenRecord] = {}
        self._user_access_index: dict[uuid.UUID, set[str]] = {}
        self._user_refresh_index: dict[uuid.UUID, set[str]] = {}

    async def _issue_tokens(self, user_id: uuid.UUID) -> TokenPair:
        async with self._lock:
            access_token = self._generate_token()
            refresh_token = self._generate_token()
            now = datetime.now(timezone.utc)
            self._access_tokens[access_token] = _TokenRecord(user_id=user_id, expires_at=now + self._access_ttl)
            self._refresh_tokens[refresh_token] = _TokenRecord(user_id=user_id, expires_at=now + self._refresh_ttl)
            self._user_access_index.setdefault(user_id, set()).add(access_token)
            self._user_refresh_index.setdefault(user_id, set()).add(refresh_token)
            return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def _get_valid_token_record(
        self,
        token: str,
        storage: dict[str, _TokenRecord],
    ) -> _TokenRecord | None:
        async with self._lock:
            record = storage.get(token)
            if record is None:
                return None
            if record.expires_at < datetime.now(timezone.utc):
                # token expired, cleanup
                self._revoke_token_locked(
                    token,
                    storage,
                    self._user_access_index if storage is self._access_tokens else self._user_refresh_index,
                )
                return None
            return record

    @staticmethod
    def _revoke_token_locked(
        token: str,
        storage: dict[str, _TokenRecord],
        index: dict[uuid.UUID, set[str]],
    ) -> None:
        record = storage.pop(token, None)
        if record is None:
            return
        user_tokens = index.get(record.user_id)
        if user_tokens is None:
            return
        user_tokens.discard(token)
        if not user_tokens:
            index.pop(record.user_id, None)

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_urlsafe(32)

    async def authenticate(self, email: str, password: str) -> TokenPair:
        async with self.uow as uow_ctx:
            user = await uow_ctx.users.get_by_email(email)
        if user is None or not user.is_active:
            raise exceptions.PermissionDeniedError("Invalid credentials")
        if not verify_password(password, salt_b64=user.password_salt, hash_b64=user.password_hash):
            raise exceptions.PermissionDeniedError("Invalid credentials")
        return await self._issue_tokens(user.id)

    async def logout(self, access_token: str) -> None:
        async with self._lock:
            record = self._access_tokens.pop(access_token, None)
            if record is None:
                return
            self._user_access_index.get(record.user_id, set()).discard(access_token)
            for refresh_token in list(self._user_refresh_index.get(record.user_id, set())):
                self._refresh_tokens.pop(refresh_token, None)
            self._user_refresh_index.pop(record.user_id, None)

    async def get_user_by_access_token(self, access_token: str) -> User:
        record = await self._get_valid_token_record(access_token, self._access_tokens)
        if record is None:
            raise exceptions.PermissionDeniedError("Access token is invalid or expired")
        async with self.uow as uow_ctx:
            user = await uow_ctx.users.get(record.user_id)
        if user is None or not user.is_active:
            raise exceptions.PermissionDeniedError("User is inactive or removed")
        return user

    async def refresh_tokens(self, access_token: str, refresh_token: str) -> TokenPair:
        refresh_record = await self._get_valid_token_record(refresh_token, self._refresh_tokens)
        if refresh_record is None:
            raise exceptions.PermissionDeniedError("Refresh token is invalid or expired")
        access_record = await self._get_valid_token_record(access_token, self._access_tokens)
        if access_record is not None and access_record.user_id != refresh_record.user_id:
            raise exceptions.PermissionDeniedError("Tokens belong to different users")
        async with self._lock:
            self._revoke_token_locked(access_token, self._access_tokens, self._user_access_index)
            self._revoke_token_locked(refresh_token, self._refresh_tokens, self._user_refresh_index)
        return await self._issue_tokens(refresh_record.user_id)
