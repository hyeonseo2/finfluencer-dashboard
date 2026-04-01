from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin token")


def get_disclaimer() -> str:
    from app.schemas.schemas import DISCLAIMER

    return DISCLAIMER
