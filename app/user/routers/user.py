# app/user/routers/user.py
from __future__ import annotations

from fastapi import APIRouter

from app.user.routers import user_routes_auth
from app.user.routers import user_routes_me

router = APIRouter(prefix="/users", tags=["users"])


def _register_all_routes() -> None:
    user_routes_auth.register(router)
    user_routes_me.register(router)


_register_all_routes()
