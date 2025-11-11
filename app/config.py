from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    name: str = Field(default="rate-limit-service")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    log_level: str = Field(default="INFO")
    default_limit: int = Field(default=100)
    default_window_minutes: int = Field(default=60)
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class RedisConfig(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    ssl: bool = Field(default=False)
    decode_responses: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Config(BaseSettings):
    app: AppConfig = Field(default_factory=AppConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def load_config() -> Config:
    return Config()





