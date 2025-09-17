from pydantic import BaseModel, Field, computed_field, model_validator


class PostgresSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5432)
    database: str = Field(default="digitalsec_integration")
    user: str = Field(default="digitalsec_username")
    password: str = Field(default="digitalsec_password")
    automigrate: bool = Field(default=True)


class RouterServiceRetrySettings(BaseModel):
    attempts: int = Field(default=3, ge=1)
    wait_initial: float = Field(default=0.5, ge=0)
    wait_max: float = Field(default=10.0, ge=0)
    wait_multiplier: float = Field(default=2.0, ge=1)
    jitter: float = Field(default=0.1, ge=0)

    @model_validator(mode="after")
    def validate_waits(self) -> "RouterServiceRetrySettings":
        if self.wait_max < self.wait_initial:
            raise ValueError("wait_max must be greater than or equal to wait_initial")
        return self


class RouterServiceSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    timeout: int = Field(default=30)
    retry: RouterServiceRetrySettings = Field(default_factory=RouterServiceRetrySettings)

    @computed_field
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ExternalSettings(BaseModel):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    router_service: RouterServiceSettings = Field(default_factory=RouterServiceSettings)
