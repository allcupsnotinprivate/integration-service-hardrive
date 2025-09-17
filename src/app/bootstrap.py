from loguru import logger

from app.configs import Settings
from app.exceptions import DuplicateError
from app.service_layer import AUsersService


async def run_bootstrap(*, settings: Settings, users_service: AUsersService) -> None:
    bootstrap_settings = settings.internal.bootstrap
    if not bootstrap_settings.enabled:
        logger.info("Bootstrap is disabled; skipping user creation")
        return

    user_settings = bootstrap_settings.user
    try:
        await users_service.create_user(
            username=user_settings.username,
            email=user_settings.email,
            fullname=user_settings.fullname,
            is_active=user_settings.is_active,
            role=user_settings.role,
            password=user_settings.password,
        )
    except DuplicateError:
        logger.info("Bootstrap user {email} already exists; skipping creation", email=user_settings.email)
    else:
        logger.info("Bootstrap user {email} has been created", email=user_settings.email)
