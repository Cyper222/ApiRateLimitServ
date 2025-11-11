import os
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_check_endpoint_with_redis(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/rate-limit/rules",
            json={"clientId": "it-client", "endpoint": "/it", "limit": 2, "windowMinutes": 1},
        )
        assert resp.status_code in (200, 503)
        if resp.status_code == 503:
            pytest.skip("Redis unavailable for integration test")

        payload = {
            "clientId": "it-client",
            "endpoint": "/it",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        r1 = await ac.post("/api/v1/rate-limit/check", json=payload)
        r2 = await ac.post("/api/v1/rate-limit/check", json=payload)
        r3 = await ac.post("/api/v1/rate-limit/check", json=payload)
        assert r1.status_code == 200 and r2.status_code == 200 and r3.status_code == 200
        assert r1.json()["allowed"] is True
        assert r2.json()["allowed"] is True
        assert r3.json()["allowed"] is False




