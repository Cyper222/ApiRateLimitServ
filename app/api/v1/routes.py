import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from redis import exceptions as redis_exceptions

from app.models.schemas import (
    CreateRuleRequest,
    CreateRuleResponse,
    RateLimitCheckRequest,
    RateLimitCheckResponse,
)
from app.services.rate_limiter import RateLimiterService, Rule
from app.storage.redis_client import get_redis_instance

logger = logging.getLogger("api")
router = APIRouter(prefix="/api/v1/rate-limit", tags=["rate-limit"])


def get_service() -> RateLimiterService:
    redis = get_redis_instance()
    if not redis:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis unavailable")
    return RateLimiterService(redis=redis, default_rule=Rule(limit=100, window_seconds=3600))


@router.post("/check", response_model=RateLimitCheckResponse)
async def check_limit(body: RateLimitCheckRequest, svc: RateLimiterService = Depends(get_service)) -> RateLimitCheckResponse:
    try:
        allowed, limit, remaining, reset_at = await svc.check_and_increment(body.clientId, body.endpoint, body.timestamp)
        return RateLimitCheckResponse(allowed=allowed, limit=limit, remaining=remaining, resetAt=reset_at)
    except redis_exceptions.RedisError:
        logger.error("redis_error_on_check", extra={"clientId": body.clientId, "endpoint": body.endpoint})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis error")


@router.post("/rules", response_model=CreateRuleResponse)
async def create_rule(body: CreateRuleRequest, svc: RateLimiterService = Depends(get_service)) -> CreateRuleResponse:
    try:
        await svc.set_rule(body.clientId, body.endpoint, body.limit, body.windowMinutes)
        return CreateRuleResponse(
            status="ok",
            clientId=body.clientId,
            endpoint=body.endpoint,
            limit=body.limit,
            windowMinutes=body.windowMinutes,
        )
    except redis_exceptions.RedisError:
        logger.error("redis_error_on_rule", extra={"clientId": body.clientId, "endpoint": body.endpoint})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis error")





