"""Request bodies. Field names are camelCase on the wire, matching the frontend."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel


class Body(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, str_strip_whitespace=True)


class SignUp(Body):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)
    organization: str = Field(min_length=1, max_length=160)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class SignIn(Body):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class ProfileUpdate(Body):
    full_name: str = Field(min_length=1, max_length=100)
    organization: str = Field(min_length=1, max_length=160)


class PasswordUpdate(Body):
    password: str = Field(min_length=8, max_length=72)


class ResetRequest(Body):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class ResetConfirm(Body):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=72)


class ReviewBody(Body):
    status: Literal["open", "confirmed", "dismissed"]
    note: Optional[str] = Field(default=None, max_length=2000)


class RepairDecision(Body):
    decision: Literal["pending", "accepted", "rejected", "edited"]
    text: Optional[str] = Field(default=None, min_length=1, max_length=5000)


YearRange = Literal["2020-", "2010-2019", "-2009"]


class SearchBody(Body):
    query: str = Field(min_length=1, max_length=5000)
    domains: Optional[list[str]] = Field(default=None, max_length=10)
    year_ranges: Optional[list[YearRange]] = Field(default=None, max_length=3)
    limit: Optional[int] = Field(default=None, ge=1, le=20)
