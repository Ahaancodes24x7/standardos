from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models as m
from .db import get_db
from .errors import Unauthorized
from .security import read_session_user_id


def optional_user_id(request: Request) -> Optional[uuid.UUID]:
    raw = read_session_user_id(request)
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def require_user_id(user_id: Optional[uuid.UUID] = Depends(optional_user_id)) -> uuid.UUID:
    if not user_id:
        raise Unauthorized()
    return user_id


def organization_of(db: Session, user_id: uuid.UUID) -> str:
    profile = db.scalar(select(m.Profile).where(m.Profile.user_id == user_id))
    return profile.organization if profile else "My workspace"


DB = Depends(get_db)
