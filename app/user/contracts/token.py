# app/user/contracts/token.py
from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int | None = Field(None, description="有效期，单位秒")
