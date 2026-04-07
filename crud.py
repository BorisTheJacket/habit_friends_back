from sqlalchemy.orm import Session
from models import User, Habit
from schemas import UserUpsert, HabitCreate, HabitUpdate
import uuid

def upsert_user(db: Session, firebase_uid: str, data: UserUpsert) -> User:
    db_user = db.query(User).filter(User.id == firebase_uid).first()
    if db_user is None:
        db_user = User(id=firebase_uid, username=data.username, email=data.email)
        db.add(db_user)
    else:
        if data.username is not None:
            db_user.username = data.username
        if data.email is not None:
            db_user.email = data.email
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, firebase_uid: str) -> User:
    return db.query(User).filter(User.id == firebase_uid).first()

def get_habit(db: Session, habit_id: str, user_id: str):
    return db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()

def get_habits(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(Habit).filter(Habit.user_id == user_id).offset(skip).limit(limit).all()

def create_habit(db: Session, habit: HabitCreate, user_id: str):
    db_habit = Habit(**habit.dict(), user_id=user_id)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

def update_habit(db: Session, habit_id: str, user_id: str, habit_update: HabitUpdate):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        for key, value in habit_update.dict(exclude_unset=True).items():
            setattr(db_habit, key, value)
        db.commit()
        db.refresh(db_habit)
    return db_habit

def update_habit_image(db: Session, habit_id: str, user_id: str, image: bytes):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        db_habit.image = image
        db.commit()
        db.refresh(db_habit)
    return db_habit

def delete_habit(db: Session, habit_id: str, user_id: str):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        db.delete(db_habit)
        db.commit()
    return db_habit