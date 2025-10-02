from typing import Self

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# app_settings: ContextVar["AppSettings"] = ContextVar("application settings")


class DatabaseSettings(BaseModel):
    user: str
    password: SecretStr
    host: str = "127.0.0.1"
    port: int = 5432
    db: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"


class JWTSettings(BaseModel):
    secret_key: SecretStr
    algorithm: str = "HS256"
    email_confirmation_ttl: int = 1
    """Token expire time in days"""
    access_token_ttl: int = 1200
    """Access token expire time in seconds"""
    refresh_token_ttl: int = 1
    """Refresh token expire time in days"""


class AppSettings(BaseSettings):
    database: DatabaseSettings
    jwt: JWTSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    @classmethod
    def load(cls) -> Self:
        settings = cls()
        return settings

# def set_app_settings(settings: AppSettings):
#     app_settings.set(settings)
#
#
# def get_app_settings() -> AppSettings:
#     return app_settings.get()
