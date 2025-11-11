from typing import Optional

from redis.asyncio import Redis

from app.config import RedisConfig


_redis_instance: Optional[Redis] = None


def get_redis_instance() -> Optional[Redis]:
    return _redis_instance


async def init_redis(cfg: RedisConfig) -> Redis:
    global _redis_instance
    _redis_instance = Redis(
        host=cfg.host,
        port=cfg.port,
        db=cfg.db,
        ssl=cfg.ssl,
        decode_responses=cfg.decode_responses,
    )
    await _redis_instance.ping()
    return _redis_instance


async def close_redis() -> None:
    global _redis_instance
    if _redis_instance:
        await _redis_instance.close()
        _redis_instance = None




