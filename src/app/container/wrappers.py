from app.configs import Settings
from app.infrastructure import PostgresDatabase
from app.infrastructure.router_service import RouterServiceHTTPClient
from app.service_layer import AUnitOfWork, AuthService


class PostgresDatabaseWrapper(PostgresDatabase):
    def __init__(self, settings: Settings):
        pg = settings.external.postgres
        super().__init__(
            user=pg.user,
            password=pg.password,
            host=pg.host,
            port=pg.port,
            database=pg.database,
            automigrate=pg.automigrate,
        )


class RouterServiceHTTPClientWrapper(RouterServiceHTTPClient):
    def __init__(self, settings: Settings):
        section = settings.external.router_service
        super().__init__(
            base_url=section.url,  # type: ignore[arg-type]
            timeout=section.timeout,
            retry_attempts=section.retry.attempts,
            retry_backoff_initial=section.retry.wait_initial,
            retry_backoff_max=section.retry.wait_max,
            retry_backoff_multiplier=section.retry.wait_multiplier,
            retry_jitter=section.retry.jitter,
        )


class AuthServiceWrapper(AuthService):
    def __init__(self, settings: Settings, uow: AUnitOfWork):
        section = settings.internal.auth
        super().__init__(access_ttl=section.access_token_ttl, refresh_ttl=section.refresh_token_ttl, uow=uow)
