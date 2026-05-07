from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import (
    create_friend_request,
    get_incoming_requests,
    accept_friend_request,
    reject_friend_request,
    get_friends,
    get_friend_habits,
    get_user,
)
from notifications import send_invite_notification
from schemas import (
    FriendRequestCreate,
    FriendRequestResponse,
    UserResponse,
    FriendHabitResponse,
    ActivityFeedItemResponse,
    ActivityHabitResponse,
)
from auth import get_current_user
from notifications import send_invite_notification

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/request", response_model=FriendRequestResponse)
async def send_friend_request(
    body: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if body.to_user_id == current_user:
        raise HTTPException(
            status_code=400, detail="Cannot send friend request to yourself"
        )
    try:
        result = create_friend_request(
            db=db, from_user_id=current_user, to_user_id=body.to_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if result is None:
        raise HTTPException(status_code=400, detail="Request failed")

    sender = get_user(db, firebase_uid=current_user)
    sender_name = (sender.username if sender and sender.username else "Someone")
    await send_invite_notification(
        external_ids=[body.to_user_id],
        type_="friend_request",
        title="New friend request",
        body=f"{sender_name} sent you a friend request",
        data={"request_id": result.id, "from_user_id": current_user},
    )

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
    return [
        {
            "user": item["user"],
            "habit": {
                "id": item["habit"].id,
                "name": item["habit"].name,
                "days": item["habit"].days,
                "image": item["habit"].image,
                "is_small": item["habit"].is_small,
                "date": item["habit"].date.isoformat() if hasattr(item["habit"].date, "isoformat") else item["habit"].date,
                "is_mutual": bool(item["habit"].requires_mutual_confirmation),
                "completed_this_week": item["completed_this_week"],
            },
        }
        for item in get_friend_habits(db, current_user)
    ]