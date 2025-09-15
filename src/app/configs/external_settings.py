from pydantic import BaseModel, Field, computed_field


class PostgresSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5432)
    database: str = Field(default="digitalsec_integration")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    automigrate: bool = Field(default=True)


class RouterServiceSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    timeout: int = Field(default=30)

    @computed_field
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ExternalSettings(BaseModel):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    router_service: RouterServiceSettings = Field(default_factory=RouterServiceSettings)
