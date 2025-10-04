from typing import Self

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = (
    "DatabaseSettings",
    "JWTSettings",
    "AppSettings",
)


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    user: str
    """Database username"""
    password: SecretStr
    """Database password"""
    host: str = "127.0.0.1"
    """Database host address"""
    port: int = 5432
    """Database port"""
    db: str
    """Database name"""

    @property
    def async_postgres_url(self) -> str:
        """
        Generate PostgreSQL database URL for asyncpg driver.

        Returns:
            PostgreSQL connection URL in format:
            postgresql+asyncpg://user:password@host:port/db
        """
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"


class JWTSettings(BaseModel):
    """JWT token configuration settings."""
    secret_key: SecretStr
    """Secret key for JWT token signing and verification"""
    algorithm: str = "HS256"
    """JWT signing algorithm"""
    email_confirmation_ttl: int = 1
    """Email confirmation token expiry in days"""
    access_token_ttl: int = 1200
    """Access token expiry in seconds (20 minutes)"""
    refresh_token_ttl: int = 1
    """Refresh token expiry in days"""


class AppSettings(BaseSettings):
    """Main application settings configuration.

    Combines database and JWT settings with environment configuration.
    """
    database: DatabaseSettings
    """Database configuration settings"""
    jwt: JWTSettings
    """JWT token configuration settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    @classmethod
    def load(cls) -> Self:
        """Load application settings from environment variables."""
        return cls()
