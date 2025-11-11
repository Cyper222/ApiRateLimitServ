import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from redis.asyncio import Redis


logger = logging.getLogger("rate_limiter")


@dataclass
class Rule:
    limit: int
    window_seconds: int


class RateLimiterService:
    def __init__(self, redis: Redis, default_rule: Rule) -> None:
        self.redis = redis
        self.default_rule = default_rule
        self.rules_hash_key = "rl:rules"

    @staticmethod
    def _rule_field(client_id: Optional[str], endpoint: Optional[str]) -> str:
        c = client_id or "default"
        e = endpoint or "default"
        return f"{c}|{e}"

    async def set_rule(self, client_id: Optional[str], endpoint: Optional[str], limit: int, window_minutes: int) -> None:
        field = self._rule_field(client_id, endpoint)
        value = json.dumps({"limit": limit, "window_seconds": window_minutes * 60})
        await self.redis.hset(self.rules_hash_key, field, value)
        logger.info("rule_set", extra={"clientId": client_id, "endpoint": endpoint, "limit": limit, "windowMinutes": window_minutes})

    async def get_rule(self, client_id: str, endpoint: str) -> Rule:
        # Try specific client+endpoint
        for c, e in [(client_id, endpoint), (client_id, "default"), ("default", endpoint), ("default", "default")]:
            field = self._rule_field(c if c != "default" else None, e if e != "default" else None)
            raw = await self.redis.hget(self.rules_hash_key, field)
            if raw:
                data = json.loads(raw)
                return Rule(limit=int(data["limit"]), window_seconds=int(data["window_seconds"]))
        return self.default_rule

    @staticmethod
    def _key(client_id: str, endpoint: str) -> str:
        return f"rl:win:{client_id}:{endpoint}"

    @staticmethod
    def _to_epoch_seconds(dt: datetime) -> int:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return int(dt.timestamp())

    async def check_and_increment(self, client_id: str, endpoint: str, at: datetime) -> Tuple[bool, int, int, datetime]:
        rule = await self.get_rule(client_id, endpoint)
        window = rule.window_seconds
        limit = rule.limit
        key = self._key(client_id, endpoint)
        now = self._to_epoch_seconds(at)
        min_score = now - window + 1

        pipe = self.redis.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", min_score - 1)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.zrange(key, 0, 0, withscores=True)
        pipe.expire(key, window)
        results = await pipe.execute()

        current_count = int(results[2])
        oldest = results[3]
        if oldest and len(oldest) > 0:
            oldest_ts = int(oldest[0][1])
        else:
            oldest_ts = now

        allowed = current_count <= limit
        remaining = max(0, limit - current_count)
        reset_at_epoch = oldest_ts + window
        reset_at = datetime.fromtimestamp(reset_at_epoch, tz=timezone.utc)

        logger.info(
            "rate_check",
            extra={
                "clientId": client_id,
                "endpoint": endpoint,
                "allowed": allowed,
                "limit": limit,
                "remaining": remaining,
                "windowSeconds": window,
            },
        )
        return allowed, limit, remaining, reset_at





