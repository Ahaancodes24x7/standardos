"""Accounts: sign-up, sign-in, session, profile and password reset."""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import optional_user_id, require_user_id
from ..errors import AppError, Unauthorized
from ..schemas import PasswordUpdate, ProfileUpdate, ResetConfirm, ResetRequest, SignIn, SignUp
from ..security import clear_session, hash_password, hash_token, set_session, verify_password
from ..store import now

router = APIRouter(prefix="/api/auth", tags=["auth"])

RESET_TOKEN_TTL = timedelta(hours=1)


def current_user(db: Session, user_id: uuid.UUID) -> Optional[dict[str, Any]]:
    user = db.get(m.User, user_id)
    if not user:
        return None
    profile = db.scalar(select(m.Profile).where(m.Profile.user_id == user_id))
    return {
        "id": str(user.id),
        "email": user.email,
        "profile": (
            {"full_name": profile.full_name, "organization": profile.organization}
            if profile
            else {"full_name": user.email.split("@")[0] or "User", "organization": "My workspace"}
        ),
    }


@router.get("/me")
def me(user_id: Optional[uuid.UUID] = Depends(optional_user_id), db: Session = Depends(get_db)):
    return current_user(db, user_id) if user_id else None


@router.post("/signup")
def sign_up(body: SignUp, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(m.User).where(m.User.email == body.email)):
        raise AppError("An account with this email already exists.")
    user = m.User(email=body.email, password_hash=hash_password(body.password))
    try:
        db.add(user)
        db.flush()
        db.add(m.Profile(user_id=user.id, full_name=body.full_name, organization=body.organization))
        db.commit()
    except IntegrityError as exc:  # unique_violation race between the check and the insert
        db.rollback()
        raise AppError("An account with this email already exists.") from exc
    set_session(response, str(user.id))
    return {
        "id": str(user.id),
        "email": user.email,
        "profile": {"full_name": body.full_name, "organization": body.organization},
    }


@router.post("/signin")
def sign_in(body: SignIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise AppError("Invalid email or password.", 401)
    set_session(response, str(user.id))
    return current_user(db, user.id)


@router.post("/signout")
def sign_out(response: Response):
    clear_session(response)
    return None


@router.patch("/profile")
def update_profile(body: ProfileUpdate, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    profile = db.scalar(select(m.Profile).where(m.Profile.user_id == user_id))
    if not profile:
        if not db.get(m.User, user_id):
            raise Unauthorized()
        profile = m.Profile(user_id=user_id, full_name=body.full_name, organization=body.organization)
        db.add(profile)
    profile.full_name = body.full_name
    profile.organization = body.organization
    profile.updated_at = now()
    db.commit()
    return {"full_name": body.full_name, "organization": body.organization}


@router.post("/password")
def update_password(body: PasswordUpdate, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    user = db.get(m.User, user_id)
    if not user:
        raise Unauthorized()
    user.password_hash = hash_password(body.password)
    db.commit()
    return {"ok": True}


@router.post("/password-reset/request")
def request_password_reset(body: ResetRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == body.email))
    # Always answer ok, so the endpoint does not reveal which emails are registered.
    if not user:
        return {"ok": True}
    token = secrets.token_hex(32)
    db.add(m.PasswordResetToken(user_id=user.id, token_hash=hash_token(token), expires_at=now() + RESET_TOKEN_TTL))
    db.commit()
    # No email provider is configured yet, so the link is returned directly
    # (see src/routes/forgot-password.tsx).
    return {"ok": True, "resetUrl": f"/reset-password?token={token}"}


@router.post("/password-reset/confirm")
def reset_password(body: ResetConfirm, db: Session = Depends(get_db)):
    record = db.scalar(select(m.PasswordResetToken).where(m.PasswordResetToken.token_hash == hash_token(body.token)))
    if not record or record.used_at or record.expires_at < now():
        raise AppError("This reset link is invalid or has expired.")
    user = db.get(m.User, record.user_id)
    if not user:
        raise AppError("This reset link is invalid or has expired.")
    user.password_hash = hash_password(body.password)
    record.used_at = now()
    db.commit()
    return {"ok": True}
