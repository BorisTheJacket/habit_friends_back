from sqlalchemy.orm import Session
from models import (
    User,
    Habit,
    FriendRequest,
    HabitInvitation,
    HabitCompletion,
    MutualDayConfirmation,
)
from schemas import UserUpsert, HabitCreate, HabitUpdate, FriendRequestCreate, FriendRequestResponse
import uuid
from datetime import datetime, timedelta


# --- Users (unchanged logic) ---

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
        if data.avatar is not None:
            db_user.avatar = data.avatar
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, firebase_uid: str) -> User:
    return db.query(User).filter(User.id == firebase_uid).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def delete_user(db: Session, firebase_uid: str):
    db.query(Habit).filter(Habit.user_id == firebase_uid).delete()
    db_user = db.query(User).filter(User.id == firebase_uid).first()
    if db_user:
        db.delete(db_user)
    db.commit()


# --- Habits ---

def get_habit(db: Session, habit_id: str, user_id: str):
    return db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()


def get_habits(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(Habit).filter(Habit.user_id == user_id).offset(skip).limit(limit).all()


def create_habit(db: Session, habit: HabitCreate, user_id: str):
    data = habit.dict()
    if data.get("requires_mutual_confirmation"):
        data["mutual_group_id"] = str(uuid.uuid4())
    else:
        data["mutual_group_id"] = None
    db_habit = Habit(**data, user_id=user_id)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit


def update_habit(db: Session, habit_id: str, user_id: str, habit_update: HabitUpdate):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        patch = habit_update.dict(exclude_unset=True)
        turning_off = patch.get("requires_mutual_confirmation") is False
        for key, value in patch.items():
            setattr(db_habit, key, value)
        if turning_off:
            db_habit.mutual_group_id = None
        if patch.get("requires_mutual_confirmation") is True and not db_habit.mutual_group_id:
            db_habit.mutual_group_id = str(uuid.uuid4())
        db.commit()
        db.refresh(db_habit)
        return db_habit
    return None


def update_habit_image(db: Session, habit_id: str, user_id: str, image: bytes):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        db_habit.image = image
        db.commit()
        db.refresh(db_habit)
        return db_habit
    return None


def delete_habit(db: Session, habit_id: str, user_id: str):
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if db_habit:
        mg = db_habit.mutual_group_id
        db.query(HabitInvitation).filter(HabitInvitation.habit_id == habit_id).delete()
        db.delete(db_habit)
        db.commit()
        if mg:
            _cleanup_mutual_group_if_orphan(db, mg)
        return db_habit
    return None


def _cleanup_mutual_group_if_orphan(db: Session, mutual_group_id: str):
    remaining = db.query(Habit).filter(Habit.mutual_group_id == mutual_group_id).count()
    if remaining == 0:
        db.query(MutualDayConfirmation).filter(
            MutualDayConfirmation.mutual_group_id == mutual_group_id
        ).delete()
        db.commit()


# --- Friend requests (unchanged) ---

def create_friend_request(db: Session, from_user_id: str, to_user_id: str):
    if from_user_id == to_user_id:
        raise ValueError("Cannot send friend request to yourself")
    existing = (
        db.query(FriendRequest)
        .filter(
            (
                (FriendRequest.from_user_id == from_user_id)
                & (FriendRequest.to_user_id == to_user_id)
            )
            | (
                (FriendRequest.from_user_id == to_user_id)
                & (FriendRequest.to_user_id == from_user_id)
            )
        )
        .filter(FriendRequest.status.in_(["pending", "accepted"]))
        .first()
    )
    if existing:
        raise ValueError("Friend request already exists")
    request = FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_incoming_requests(db: Session, user_id: str):
    return (
        db.query(FriendRequest)
        .filter(FriendRequest.to_user_id == user_id, FriendRequest.status == "pending")
        .all()
    )


def accept_friend_request(db: Session, request_id: str, user_id: str):
    request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.id == request_id,
            FriendRequest.to_user_id == user_id,
            FriendRequest.status == "pending",
        )
        .first()
    )
    if request:
        request.status = "accepted"
        db.commit()
        db.refresh(request)
        return request
    return None


def reject_friend_request(db: Session, request_id: str, user_id: str):
    request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.id == request_id,
            FriendRequest.to_user_id == user_id,
            FriendRequest.status == "pending",
        )
        .first()
    )
    if request:
        request.status = "rejected"
        db.commit()
        db.refresh(request)
        return request
    return None


def get_friends(db: Session, user_id: str):
    requests = (
        db.query(FriendRequest)
        .filter(
            ((FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id))
            & (FriendRequest.status == "accepted")
        )
        .all()
    )
    friend_ids = []
    for req in requests:
        if req.from_user_id == user_id:
            friend_ids.append(req.to_user_id)
        else:
            friend_ids.append(req.from_user_id)
    return db.query(User).filter(User.id.in_(friend_ids)).all()


def get_friend_habits(db: Session, user_id: str):
    requests = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.status == "accepted",
            (FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id),
        )
        .all()
    )
    friend_ids = []
    for req in requests:
        if req.from_user_id == user_id:
            friend_ids.append(req.to_user_id)
        else:
            friend_ids.append(req.from_user_id)

    if not friend_ids:
        return []

    habits = db.query(Habit).filter(Habit.user_id.in_(friend_ids)).all()
    users = db.query(User).filter(User.id.in_(friend_ids)).all()
    user_map = {user.id: user for user in users}

    result = []
    for habit in habits:
        user = user_map.get(habit.user_id)
        if user:
            result.append({"user": user, "habit": habit})
    return result


# --- Habit invitations ---

def create_habit_invitations(db: Session, habit_id: str, from_user_id: str, friend_ids: list[str]):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == from_user_id).first()
    if not habit:
        raise ValueError("Habit not found")

    created = []
    for friend_id in friend_ids:
        if friend_id == from_user_id:
            continue
        existing = (
            db.query(HabitInvitation)
            .filter(
                HabitInvitation.habit_id == habit_id,
                HabitInvitation.to_user_id == friend_id,
                HabitInvitation.status == "pending",
            )
            .first()
        )
        if existing:
            continue
        invitation = HabitInvitation(
            habit_id=habit_id,
            from_user_id=from_user_id,
            to_user_id=friend_id,
        )
        db.add(invitation)
        created.append(invitation)
    db.commit()
    for inv in created:
        db.refresh(inv)
    return created


def get_incoming_habit_invitations(db: Session, user_id: str):
    return (
        db.query(HabitInvitation)
        .filter(
            HabitInvitation.to_user_id == user_id,
            HabitInvitation.status == "pending",
        )
        .all()
    )


def accept_habit_invitation(db: Session, invitation_id: str, user_id: str):
    invitation = (
        db.query(HabitInvitation)
        .filter(
            HabitInvitation.id == invitation_id,
            HabitInvitation.to_user_id == user_id,
            HabitInvitation.status == "pending",
        )
        .first()
    )
    if not invitation:
        return None

    invitation.status = "accepted"

    original_habit = db.query(Habit).filter(Habit.id == invitation.habit_id).first()
    if original_habit:
        new_habit = Habit(
            user_id=user_id,
            name=original_habit.name,
            days=original_habit.days,
            image=original_habit.image,
            is_small=original_habit.is_small,
            date=original_habit.date,
            selected_days=original_habit.selected_days,
            reminder_time=original_habit.reminder_time,
            is_reminding=original_habit.is_reminding,
            level=1,
            is_archived=False,
            requires_mutual_confirmation=original_habit.requires_mutual_confirmation,
            mutual_group_id=original_habit.mutual_group_id,
        )
        db.add(new_habit)

    db.commit()
    db.refresh(invitation)
    return invitation


def reject_habit_invitation(db: Session, invitation_id: str, user_id: str):
    invitation = (
        db.query(HabitInvitation)
        .filter(
            HabitInvitation.id == invitation_id,
            HabitInvitation.to_user_id == user_id,
            HabitInvitation.status == "pending",
        )
        .first()
    )
    if not invitation:
        return None

    invitation.status = "rejected"
    db.commit()
    db.refresh(invitation)
    return invitation


# --- Mutual helpers ---

def _habits_in_group(db: Session, mutual_group_id: str) -> list[Habit]:
    return db.query(Habit).filter(Habit.mutual_group_id == mutual_group_id).all()


def _expected_member_ids(db: Session, mutual_group_id: str) -> set[str]:
    return {h.user_id for h in _habits_in_group(db, mutual_group_id)}


def _confirmed_user_ids_for_day(db: Session, mutual_group_id: str, date: str) -> set[str]:
    rows = (
        db.query(MutualDayConfirmation)
        .filter(
            MutualDayConfirmation.mutual_group_id == mutual_group_id,
            MutualDayConfirmation.date == date,
        )
        .all()
    )
    return {r.user_id for r in rows}


def is_mutual_day_fully_confirmed(db: Session, mutual_group_id: str, date: str) -> bool:
    expected = _expected_member_ids(db, mutual_group_id)
    if not expected:
        return False
    confirmed = _confirmed_user_ids_for_day(db, mutual_group_id, date)
    return expected == confirmed


def _finalize_mutual_day(db: Session, mutual_group_id: str, date: str):
    """Write HabitCompletion for every habit in the group (idempotent)."""
    for h in _habits_in_group(db, mutual_group_id):
        create_completion(db, habit_id=h.id, user_id=h.user_id, date=date)


def _delete_all_group_completions_for_day(db: Session, mutual_group_id: str, date: str):
    habit_ids = [h.id for h in _habits_in_group(db, mutual_group_id)]
    if not habit_ids:
        return
    (
        db.query(HabitCompletion)
        .filter(HabitCompletion.habit_id.in_(habit_ids), HabitCompletion.date == date)
        .delete(synchronize_session=False)
    )
    db.commit()


def record_mutual_confirmation(db: Session, habit: Habit, user_id: str, date: str) -> dict:
    """
    Returns dict for JSON: week_count, pending_mutual, confirmed, mutual_group_id
    """
    if not habit.mutual_group_id:
        create_completion(db, habit_id=habit.id, user_id=user_id, date=date)
        ws = _week_start_str(date)
        wc = get_habit_week_completion_count(db, habit.id, user_id, ws)
        return {"week_count": wc, "pending_mutual": False, "confirmed": True, "mutual_group_id": None}

    mg = habit.mutual_group_id
    existing = (
        db.query(MutualDayConfirmation)
        .filter(
            MutualDayConfirmation.mutual_group_id == mg,
            MutualDayConfirmation.date == date,
            MutualDayConfirmation.user_id == user_id,
        )
        .first()
    )
    if not existing:
        db.add(
            MutualDayConfirmation(
                mutual_group_id=mg,
                date=date,
                user_id=user_id,
            )
        )
        db.commit()

    if is_mutual_day_fully_confirmed(db, mg, date):
        _finalize_mutual_day(db, mg, date)
        pending = False
        confirmed = True
    else:
        pending = True
        confirmed = False

    ws = _week_start_str(date)
    wc = get_habit_week_completion_count(db, habit.id, user_id, ws)
    return {
        "week_count": wc,
        "pending_mutual": pending,
        "confirmed": confirmed,
        "mutual_group_id": mg,
    }


def withdraw_mutual_confirmation(db: Session, habit: Habit, user_id: str, date: str) -> None:
    if not habit.mutual_group_id:
        delete_completion(db, habit_id=habit.id, user_id=user_id, date=date)
        return

    mg = habit.mutual_group_id
    row = (
        db.query(MutualDayConfirmation)
        .filter(
            MutualDayConfirmation.mutual_group_id == mg,
            MutualDayConfirmation.date == date,
            MutualDayConfirmation.user_id == user_id,
        )
        .first()
    )
    if row:
        db.delete(row)
        db.commit()

    had_completions = (
        db.query(HabitCompletion)
        .join(Habit, Habit.id == HabitCompletion.habit_id)
        .filter(Habit.mutual_group_id == mg, HabitCompletion.date == date)
        .first()
        is not None
    )
    if had_completions and not is_mutual_day_fully_confirmed(db, mg, date):
        _delete_all_group_completions_for_day(db, mg, date)


# --- Habit completions ---

def create_completion(db: Session, habit_id: str, user_id: str, date: str):
    existing = (
        db.query(HabitCompletion)
        .filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.user_id == user_id,
            HabitCompletion.date == date,
        )
        .first()
    )
    if existing:
        return existing

    completion = HabitCompletion(habit_id=habit_id, user_id=user_id, date=date)
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion


def delete_completion(db: Session, habit_id: str, user_id: str, date: str):
    completion = (
        db.query(HabitCompletion)
        .filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.user_id == user_id,
            HabitCompletion.date == date,
        )
        .first()
    )
    if completion:
        db.delete(completion)
        db.commit()
        return completion
    return None


def _week_start_str(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    week_start = date_obj - timedelta(days=date_obj.weekday())
    return week_start.strftime("%Y-%m-%d")


def get_habit_week_completion_count(db: Session, habit_id: str, user_id: str, week_start: str) -> int:
    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=7)
    end_str = end.strftime("%Y-%m-%d")

    return (
        db.query(HabitCompletion)
        .filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.user_id == user_id,
            HabitCompletion.date >= week_start,
            HabitCompletion.date < end_str,
        )
        .count()
    )


def get_week_completions(db: Session, user_id: str, week_start: str):
    """
    Returns list of dicts: { habit_id, date, pending_mutual }
    """
    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=7)
    end_str = end.strftime("%Y-%m-%d")

    finalized = (
        db.query(HabitCompletion)
        .filter(
            HabitCompletion.user_id == user_id,
            HabitCompletion.date >= week_start,
            HabitCompletion.date < end_str,
        )
        .all()
    )
    out: list[dict] = [
        {"habit_id": r.habit_id, "date": r.date, "pending_mutual": False} for r in finalized
    ]

    my_mutual_habits = (
        db.query(Habit)
        .filter(
            Habit.user_id == user_id,
            Habit.requires_mutual_confirmation.is_(True),
            Habit.mutual_group_id.isnot(None),
        )
        .all()
    )

    for habit in my_mutual_habits:
        mg = habit.mutual_group_id
        if not mg:
            continue
        pending_rows = (
            db.query(MutualDayConfirmation)
            .filter(
                MutualDayConfirmation.mutual_group_id == mg,
                MutualDayConfirmation.user_id == user_id,
                MutualDayConfirmation.date >= week_start,
                MutualDayConfirmation.date < end_str,
            )
            .all()
        )
        for pr in pending_rows:
            already = (
                db.query(HabitCompletion)
                .filter(
                    HabitCompletion.habit_id == habit.id,
                    HabitCompletion.user_id == user_id,
                    HabitCompletion.date == pr.date,
                )
                .first()
            )
            if already:
                continue
            if not is_mutual_day_fully_confirmed(db, mg, pr.date):
                out.append(
                    {"habit_id": habit.id, "date": pr.date, "pending_mutual": True}
                )

    return out


def advance_habit(db: Session, habit_id: str, user_id: str):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return None

    habit.level += 1
    if habit.level > 3:
        habit.is_archived = True

    db.commit()
    db.refresh(habit)
    return habit


def reset_habit_level(db: Session, habit_id: str, user_id: str):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return None

    habit.level = 1
    db.commit()
    db.refresh(habit)
    return habit