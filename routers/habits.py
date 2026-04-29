from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import (
    get_habit,
    get_habits,
    create_habit,
    update_habit,
    delete_habit,
    update_habit_image,
    create_habit_invitations,
    get_incoming_habit_invitations,
    accept_habit_invitation,
    reject_habit_invitation,
    create_completion,
    delete_completion,
    get_week_completions,
    advance_habit,
    get_habit_week_completion_count,
    reset_habit_level,
    record_mutual_confirmation,
    withdraw_mutual_confirmation,
    get_habit_members,
)
from schemas import (
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    HabitInvitationCreate,
    HabitInvitationOut,
    CompletionRequest,
    CompletionResponse,
    WeekCompletionsResponse,
    UserResponse,
)
from auth import get_current_user
from models import Habit

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
    current_user: str = Depends(get_current_user),
):
    return create_habit(db=db, habit=habit, user_id=current_user)


@router.get("/", response_model=list[HabitResponse])
def read_habits(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return get_habits(db, user_id=current_user, skip=skip, limit=limit)


@router.get("/invitations/incoming", response_model=list[HabitInvitationOut])
def list_incoming_habit_invitations(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    invitations = get_incoming_habit_invitations(db, user_id=current_user)
    result = []
    for inv in invitations:
        habit = db.query(Habit).filter(Habit.id == inv.habit_id).first()
        result.append(
            HabitInvitationOut(
                id=inv.id,
                habit_id=inv.habit_id,
                habit_name=habit.name if habit else "Unknown",
                habit_image=habit.image if habit else None,
                habit_days=habit.days if habit else 0,
                from_user=inv.from_user,
                status=inv.status,
                created_at=inv.created_at,
            )
        )
    return result


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = accept_habit_invitation(db, invitation_id=invitation_id, user_id=current_user)
    if result is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return {"detail": "Invitation accepted"}


@router.post("/invitations/{invitation_id}/reject")
def reject_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = reject_habit_invitation(db, invitation_id=invitation_id, user_id=current_user)
    if result is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return {"detail": "Invitation rejected"}


@router.get("/completions", response_model=WeekCompletionsResponse)
def list_week_completions(
    week_start: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    rows = get_week_completions(db, user_id=current_user, week_start=week_start)
    return WeekCompletionsResponse(
        completions=[
            CompletionResponse(
                habit_id=r["habit_id"],
                date=r["date"],
                pending_mutual=r["pending_mutual"],
            )
            for r in rows
        ]
    )


@router.post("/{habit_id}/invite")
def invite_friends_to_habit(
    habit_id: str,
    body: HabitInvitationCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        created = create_habit_invitations(
            db,
            habit_id=habit_id,
            from_user_id=current_user,
            friend_ids=body.friend_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"detail": f"{len(created)} invitation(s) sent"}


@router.get("/{habit_id}/members", response_model=list[UserResponse])
def list_habit_members(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return get_habit_members(db, habit_id=habit_id, requesting_user_id=current_user)


@router.get("/{habit_id}", response_model=HabitResponse)
def read_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
):
    db_habit = update_habit_image(db, habit_id=habit_id, user_id=current_user, image=image.file.read())
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit


@router.delete("/{habit_id}")
def delete_existing_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    db_habit = delete_habit(db, habit_id=habit_id, user_id=current_user)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"detail": "Habit deleted"}


@router.post("/{habit_id}/complete")
def complete_habit(
    habit_id: str,
    body: CompletionRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    habit = get_habit(db, habit_id=habit_id, user_id=current_user)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    if habit.requires_mutual_confirmation and habit.mutual_group_id:
        raise HTTPException(
            status_code=400,
            detail="This habit uses mutual confirmation; use POST /habits/{id}/complete-mutual",
        )

    create_completion(db, habit_id=habit_id, user_id=current_user, date=body.date)
    week_start_str = _week_start_str(body.date)
    count = get_habit_week_completion_count(
        db, habit_id=habit_id, user_id=current_user, week_start=week_start_str
    )
    return {"detail": "Completed", "week_count": count, "pending_mutual": False, "confirmed": True}


@router.delete("/{habit_id}/complete")
def uncomplete_habit(
    habit_id: str,
    body: CompletionRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    habit = get_habit(db, habit_id=habit_id, user_id=current_user)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    if habit.requires_mutual_confirmation and habit.mutual_group_id:
        raise HTTPException(
            status_code=400,
            detail="This habit uses mutual confirmation; use DELETE /habits/{id}/complete-mutual",
        )

    result = delete_completion(db, habit_id=habit_id, user_id=current_user, date=body.date)
    if not result:
        raise HTTPException(status_code=404, detail="Completion not found")
    return {"detail": "Completion removed"}


def _week_start_str(date_str: str) -> str:
    from datetime import datetime, timedelta

    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    week_start = date_obj - timedelta(days=date_obj.weekday())
    return week_start.strftime("%Y-%m-%d")


@router.post("/{habit_id}/complete-mutual")
def complete_habit_mutual(
    habit_id: str,
    body: CompletionRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    habit = get_habit(db, habit_id=habit_id, user_id=current_user)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if not (habit.requires_mutual_confirmation and habit.mutual_group_id):
        raise HTTPException(status_code=400, detail="Not a mutual habit")

    payload = record_mutual_confirmation(db, habit=habit, user_id=current_user, date=body.date)
    return {"detail": "OK", **payload}


@router.delete("/{habit_id}/complete-mutual")
def uncomplete_habit_mutual(
    habit_id: str,
    body: CompletionRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    habit = get_habit(db, habit_id=habit_id, user_id=current_user)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if not (habit.requires_mutual_confirmation and habit.mutual_group_id):
        raise HTTPException(status_code=400, detail="Not a mutual habit")

    withdraw_mutual_confirmation(db, habit=habit, user_id=current_user, date=body.date)
    week_start_str = _week_start_str(body.date)
    count = get_habit_week_completion_count(
        db, habit_id=habit_id, user_id=current_user, week_start=week_start_str
    )
    return {"detail": "Mutual completion withdrawn", "week_count": count}


@router.post("/{habit_id}/advance", response_model=HabitResponse)
def advance_habit_level(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    habit = advance_habit(db, habit_id=habit_id, user_id=current_user)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.post("/{habit_id}/reset")
def reset_habit_level_route(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    habit = reset_habit_level(db, habit_id=habit_id, user_id=current_user)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.get("/{habit_id}/members", response_model=list[UserPublicResponse])
async def get_habit_members(
    habit_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get the habit and verify the caller is a member
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Only members of the mutual group can see the list
    if habit.mutual_group_id is None:
        return []

    # Fetch all habits in the same mutual group
    group_result = await db.execute(
        select(Habit).where(
            Habit.mutual_group_id == habit.mutual_group_id,
            Habit.is_archived == False,
        )
    )
    group_habits = group_result.scalars().all()

    # Collect user IDs (excluding the caller)
    member_user_ids = [h.user_id for h in group_habits if h.user_id != current_user.id]

    if not member_user_ids:
        return []

    users_result = await db.execute(
        select(User).where(User.id.in_(member_user_ids))
    )
    members = users_result.scalars().all()
    return members