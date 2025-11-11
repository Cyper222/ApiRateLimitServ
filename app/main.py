import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis import exceptions as redis_exceptions
from app.api.v1.routes import router as v1_router
from app.config import Config, load_config
from app.logging import setup_logging
from app.services.rate_limiter import RateLimiterService, Rule
from app.storage.redis_client import close_redis, get_redis_instance, init_redis


cfg: Config = load_config()
setup_logging(cfg.app.log_level)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await init_redis(cfg.redis)
        logger.info("redis_connected", extra={"host": cfg.redis.host, "port": cfg.redis.port})
    except redis_exceptions.RedisError as ex:
        logger.error("redis_connect_failed", extra={"error": str(ex)})
    yield
    await close_redis()


app = FastAPI(title=cfg.app.name, lifespan=lifespan)
default_rule = Rule(limit=cfg.app.default_limit, window_seconds=cfg.app.default_window_minutes * 60)

app.state.default_rule = default_rule

@app.get("/health")
async def health():
    redis = get_redis_instance()
    status = "ok"
    redis_ok = False
    if redis:
        try:
            await redis.ping()
            redis_ok = True
        except redis_exceptions.RedisError:
            pass
    return JSONResponse({"status": status, "redis": "ok" if redis_ok else "down"})


app.include_router(v1_router)





