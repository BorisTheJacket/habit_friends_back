from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

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