import asyncio
from datetime import datetime, timezone, timedelta

import pytest
from redis.asyncio import Redis

from app.services.rate_limiter import RateLimiterService, Rule


class FakeRedis:
    def __init__(self):
        self.data = {}

    def pipeline(self, transaction=True):
        return FakePipeline(self)

    async def hset(self, key, field, value):
        self.data.setdefault(key, {})
        self.data[key][field] = value

    async def hget(self, key, field):
        return self.data.get(key, {}).get(field)


class FakePipeline:
    def __init__(self, parent: FakeRedis):
        self.parent = parent
        self.ops = []
        self.key = None
        self.window = None
        self.now = None
        self.min_score = None

    def zremrangebyscore(self, key, min_s, max_s):
        self.ops.append(("zrem", key, min_s, max_s))
        return self

    def zadd(self, key, mapping):
        self.ops.append(("zadd", key, mapping))
        return self

    def zcard(self, key):
        self.ops.append(("zcard", key))
        return self

    def zrange(self, key, start, end, withscores=False):
        self.ops.append(("zrange", key, start, end, withscores))
        return self

    def expire(self, key, seconds):
        self.ops.append(("expire", key, seconds))
        return self

    async def execute(self):
        zsets = self.parent.data.setdefault("zsets", {})
        results = []
        for op in self.ops:
            if op[0] == "zrem":
                _, key, _, max_s = op
                arr = zsets.get(key, [])
                zsets[key] = [(m, s) for (m, s) in arr if s >= int(max_s)]
                results.append(0)
            elif op[0] == "zadd":
                _, key, mapping = op
                arr = zsets.get(key, [])
                for member, score in mapping.items():
                    arr.append((member, int(score)))
                arr.sort(key=lambda x: x[1])
                zsets[key] = arr
                results.append(1)
            elif op[0] == "zcard":
                _, key = op
                results.append(len(zsets.get(key, [])))
            elif op[0] == "zrange":
                _, key, start, end, withscores = op
                arr = zsets.get(key, [])
                sliced = arr[start : end + 1] if end >= 0 else arr[start:]
                if withscores:
                    results.append(sliced)
                else:
                    results.append([m for (m, _) in sliced])
            elif op[0] == "expire":
                results.append(True)
        self.ops.clear()
        return results


@pytest.mark.asyncio
async def test_allows_within_limit():
    redis = FakeRedis()
    svc = RateLimiterService(redis, default_rule=Rule(limit=3, window_seconds=60))
    now = datetime.now(timezone.utc)

    for i in range(3):
        allowed, limit, remaining, reset_at = await svc.check_and_increment("c1", "/e", now)
        assert allowed is True
        assert limit == 3
        assert remaining == 3 - (i + 1)
        assert reset_at > now


@pytest.mark.asyncio
async def test_blocks_when_exceeds_limit():
    redis = FakeRedis()
    svc = RateLimiterService(redis, default_rule=Rule(limit=2, window_seconds=60))
    now = datetime.now(timezone.utc)
    await svc.check_and_increment("c1", "/e", now)
    await svc.check_and_increment("c1", "/e", now)
    allowed, _, remaining, _ = await svc.check_and_increment("c1", "/e", now)
    assert allowed is False
    assert remaining == 0




