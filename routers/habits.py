from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import get_habit, get_habits, create_habit, update_habit, delete_habit, update_habit_image
from schemas import HabitCreate, HabitUpdate, HabitResponse
from auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=HabitResponse)
def create_new_habit(
    habit: HabitCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return create_habit(db=db, habit=habit, user_id=current_user)

@router.get("/", response_model=list[HabitResponse])
def read_habits(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return get_habits(db, user_id=current_user, skip=skip, limit=limit)

@router.get("/{habit_id}", response_model=HabitResponse)
def read_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_habit = get_habit(db, habit_id=habit_id, user_id=current_user)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit

@router.put("/{habit_id}", response_model=HabitResponse)
def update_existing_habit(
    habit_id: str,
    habit: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_habit = update_habit(db, habit_id=habit_id, user_id=current_user, habit_update=habit)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit

@router.put("/{habit_id}/image", response_model=HabitResponse)
def upload_habit_image(
    habit_id: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_habit = update_habit_image(db, habit_id=habit_id, user_id=current_user, image=image.file.read())
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit

@router.delete("/{habit_id}")
def delete_existing_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_habit = delete_habit(db, habit_id=habit_id, user_id=current_user)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"detail": "Habit deleted"}