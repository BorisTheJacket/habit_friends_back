from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserUpsert(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        orm_mode = True

class HabitCreate(BaseModel):
    name: str
    days: int
    is_small: bool = False
    image: Optional[str] = None
    date: Optional[datetime] = None

class HabitUpdate(BaseModel):
    name: Optional[str] = None
    days: Optional[int] = None
    is_small: Optional[bool] = None
    image: Optional[str] = None
    date: Optional[datetime] = None

class HabitResponse(BaseModel):
    id: str
    name: str
    days: int
    image: Optional[str] = None
    is_small: bool
    date: datetime

    class Config:
        orm_mode = True

class FriendRequestResponse(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    status: str
    created_at: datetime
    from_user: Optional[UserResponse] = None
    to_user: Optional[UserResponse] = None

    class Config:
        orm_mode = True

class FriendRequestCreate(BaseModel):
    to_user_id: str

class FriendHabitResponse(BaseModel):
    user: UserResponse
    habit: HabitResponse

    class Config:
        orm_mode = True