from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class RateLimitCheckRequest(BaseModel):
    clientId: str = Field(..., min_length=1)
    endpoint: str = Field(..., min_length=1)
    timestamp: datetime


class RateLimitCheckResponse(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    resetAt: datetime


class CreateRuleRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="If omitted, applies as default rule")
    endpoint: Optional[str] = Field(None, description="If omitted, applies as default rule")
    limit: int = Field(..., gt=0)
    windowMinutes: int = Field(..., gt=0)


class CreateRuleResponse(BaseModel):
    status: str
    clientId: Optional[str]
    endpoint: Optional[str]
    limit: int
    windowMinutes: int





