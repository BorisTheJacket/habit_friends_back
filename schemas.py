from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserUpsert(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True

class HabitCreate(BaseModel):
    name: str
    days: int
    is_small: bool = False
    date: Optional[datetime] = None

class HabitUpdate(BaseModel):
    name: Optional[str] = None
    days: Optional[int] = None
    is_small: Optional[bool] = None
    date: Optional[datetime] = None

class HabitResponse(BaseModel):
    id: str
    name: str
    days: int
    image: Optional[bytes] = None
    is_small: bool
    date: datetime

    class Config:
        orm_mode = True