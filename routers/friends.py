from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import (
    create_friend_request, 
    get_incoming_requests, 
    accept_friend_request, 
    reject_friend_request,
    get_friends,
    get_friend_habits
    )
from schemas import (
    FriendRequestCreate,
    FriendRequestResponse,
    UserResponse,
    FriendHabitResponse,
    ActivityFeedItemResponse,
    ActivityHabitResponse,
)
from auth import get_current_user

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/request", response_model=FriendRequestResponse)
def send_friend_request(
    body: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if body.to_user_id == current_user:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    try:
        result = create_friend_request(db=db, from_user_id=current_user, to_user_id=body.to_user_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if result is None:
        raise HTTPException(status_code=400, detail="Request failed")
    return result


@router.get("/requests/incoming", response_model=list[FriendRequestResponse])
def list_incoming_requests(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return get_incoming_requests(db, user_id=current_user)

@router.post("/requests/{request_id}/reject", response_model=FriendRequestResponse)
def reject_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_request = reject_friend_request(db, request_id=request_id, user_id=current_user)
    if db_request is None:
        raise HTTPException(status_code=404, detail="Friend request not found")
    return db_request

@router.post("/requests/{request_id}/accept", response_model=FriendRequestResponse)
def accept_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_request = accept_friend_request(db, request_id=request_id, user_id=current_user)
    if db_request is None:
        raise HTTPException(status_code=404, detail="Friend request not found")
    return db_request

@router.get("/", response_model=list[UserResponse])
def list_friends(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return get_friends(db, user_id=current_user)

@router.get("/habits", response_model=list[ActivityFeedItemResponse])
def list_friend_habits(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    raw = get_friend_habits(db, user_id=current_user)
    result = []
    for item in raw:
        user = item["user"]
        habit = item["habit"]
        result.append(
            ActivityFeedItemResponse(
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    avatar=user.avatar,
                ),
                habit=ActivityHabitResponse(
                    id=habit.id,
                    name=habit.name,
                    days=habit.days,
                    image=habit.image,
                    is_small=habit.is_small,
                    date=habit.date.isoformat() if habit.date else "",
                    is_mutual=habit.requires_mutual_confirmation or False,
                ),
            )
        )
    return result