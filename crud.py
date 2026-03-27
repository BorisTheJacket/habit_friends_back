from sqlalchemy.orm import Session
from models import User, Habit
from schemas import UserCreate, HabitCreate, HabitUpdate
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_habit(db: Session, habit_id: str, user_id: str):
    return db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()

def get_habits(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(Habit).filter(Habit.user_id == user_id).offset(skip).limit(limit).all()

def create_habit(db: Session, habit: HabitCreate, user_id: str, image: bytes = None):
    db_habit = Habit(**habit.dict(), user_id=user_id, image=image)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

def update_habit(db: Session, habit_id: str, user_id: str, habit_update: HabitUpdate, image: bytes = None):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        update_data = habit_update.dict(exclude_unset=True)
        if image is not None:
            update_data['image'] = image
        for key, value in update_data.items():
            setattr(db_habit, key, value)
        db.commit()
        db.refresh(db_habit)
    return db_habit

def delete_habit(db: Session, habit_id: str, user_id: str):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        db.delete(db_habit)
        db.commit()
    return db_habit