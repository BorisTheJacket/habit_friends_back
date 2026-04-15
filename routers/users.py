from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import upsert_user, get_user, get_all_users
from schemas import UserUpsert, UserResponse
from auth import get_current_user
from crud import upsert_user, get_user, get_all_users, delete_user
from firebase_admin import auth as firebase_auth
from models import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return get_all_users(db, skip=skip, limit=limit)


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

@router.delete("/profile")
def delete_profile(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # Delete from DB if exists (don't fail if missing)
    delete_user(db=db, firebase_uid=current_user)
    
    # Always delete from Firebase Auth
    try:
        firebase_auth.delete_user(current_user)
    except Exception:
        pass
    
    return {"detail": "Account deleted"}


@router.get("/check-username/{username}")
def check_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    existing = db.query(User).filter(
        User.username == username,
        User.id != current_user
    ).first()
    return {"available": existing is None}