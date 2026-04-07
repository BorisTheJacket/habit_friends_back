from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import upsert_user, get_user
from schemas import UserUpsert, UserResponse
from auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/profile", response_model=UserResponse)
def upsert_profile(
    user: UserUpsert,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return upsert_user(db=db, firebase_uid=current_user, data=user)


@router.get("/profile", response_model=UserResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    db_user = get_user(db, firebase_uid=current_user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_user