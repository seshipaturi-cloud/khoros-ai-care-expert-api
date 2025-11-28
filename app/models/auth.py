from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    username: str = Field(..., min_length=3, max_length=50)
    role_ids: Optional[List[str]] = []


class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    role: Optional[str] = None
    role_ids: List[str] = []
    roles: Optional[List[dict]] = []
    company_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role: Optional[str] = None
    role_ids: List[str]
    roles: Optional[List[dict]] = []
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[str]] = None
    password: Optional[str] = Field(None, min_length=8)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class SessionInfo(BaseModel):
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_active: bool = True