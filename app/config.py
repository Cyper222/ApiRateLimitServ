import os
from dataclasses import dataclass
from typing import Any, Dict

import yaml


@dataclass
class AppConfig:
    name: str
    host: str
    port: int
    log_level: str
    default_limit: int
    default_window_minutes: int


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    ssl: bool
    decode_responses: bool


@dataclass
class Config:
    app: AppConfig
    redis: RedisConfig


def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> Config:
    root = os.getenv("APP_CONFIG_PATH", os.path.join(os.getcwd(), "application.yml"))
    data = _load_yaml(root)
    redis_host = os.getenv("REDIS_HOST", data.get("redis", {}).get("host", "localhost"))

    app_cfg = AppConfig(
        name=data.get("app", {}).get("name", "rate-limit-service"),
        host=data.get("app", {}).get("host", "0.0.0.0"),
        port=int(data.get("app", {}).get("port", 8080)),
        log_level=data.get("app", {}).get("log_level", "INFO"),
        default_limit=int(data.get("app", {}).get("default_limit", 100)),
        default_window_minutes=int(data.get("app", {}).get("default_window_minutes", 60)),
    )
    redis_cfg = RedisConfig(
        host=redis_host,
        port=int(data.get("redis", {}).get("port", 6379)),
        db=int(data.get("redis", {}).get("db", 0)),
        ssl=bool(data.get("redis", {}).get("ssl", False)),
        decode_responses=bool(data.get("redis", {}).get("decode_responses", True)),
    )
    return Config(app=app_cfg, redis=redis_cfg)




