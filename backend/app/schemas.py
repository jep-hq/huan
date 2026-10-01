from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    authentik_id: str


class User(UserBase):
    id: int
    authentik_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    name: str


class APIKey(BaseModel):
    id: int
    key: str
    name: str
    user_id: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SparkJobCreate(BaseModel):
    pass


class SparkJob(BaseModel):
    id: int
    user_id: int
    job_id: str
    status: JobStatus
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    authentik_id: Optional[str] = None
