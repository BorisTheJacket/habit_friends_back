from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import get_habit, get_habits, create_habit, update_habit, delete_habit
from schemas import HabitCreate, HabitUpdate, HabitResponse
from auth import get_current_user
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=HabitResponse)
def create_new_habit(habit: HabitCreate, image: UploadFile = File(None), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    image_data = None
    if image:
        image_data = image.file.read()
    return create_habit(db=db, habit=habit, user_id=current_user, image=image_data)

@router.get("/{habit_id}", response_model=HabitResponse)
def read_habit(habit_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_habit = get_habit(db, habit_id=habit_id, user_id=current_user)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit

@router.get("/", response_model=list[HabitResponse])
def read_habits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    habits = get_habits(db, user_id=current_user, skip=skip, limit=limit)
    return habits

@router.put("/{habit_id}", response_model=HabitResponse)
def update_existing_habit(habit_id: str, habit: HabitUpdate, image: UploadFile = File(None), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    image_data = None
    if image:
        image_data = image.file.read()
    db_habit = update_habit(db, habit_id=habit_id, user_id=current_user, habit_update=habit, image=image_data)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit

@router.delete("/{habit_id}")
def delete_existing_habit(habit_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_habit = delete_habit(db, habit_id=habit_id, user_id=current_user)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"detail": "Habit deleted"}