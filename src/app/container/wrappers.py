from app.configs import Settings
from app.infrastructure import PostgresDatabase
from app.infrastructure.router_service import RouterServiceHTTPClient


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
        super().__init__(base_url=section.url, timeout=section.timeout)
