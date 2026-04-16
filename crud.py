from sqlalchemy.orm import Session
from models import User, Habit, FriendRequest, HabitInvitation, HabitCompletion
from schemas import UserUpsert, HabitCreate, HabitUpdate, FriendRequestCreate, FriendRequestResponse
import uuid


# Users

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
    # Always delete habits, even if user record doesn't exist
    db.query(Habit).filter(Habit.user_id == firebase_uid).delete()
    db_user = db.query(User).filter(User.id == firebase_uid).first()
    if db_user:
        db.delete(db_user)
    db.commit()


// Habits

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
        db.query(HabitInvitation).filter(HabitInvitation.habit_id == habit_id).delete()
        db.delete(db_habit)
        db.commit()
    return db_habit

// Friend Requests

def create_friend_request(db: Session, from_user_id: str, to_user_id: str):
    if from_user_id == to_user_id:
        raise ValueError("Cannot send friend request to yourself")
    existing = db.query(FriendRequest).filter(
        ((FriendRequest.from_user_id == from_user_id) & (FriendRequest.to_user_id == to_user_id)) |
         ((FriendRequest.from_user_id == to_user_id) & (FriendRequest.to_user_id == from_user_id))
    ).filter(FriendRequest.status.in_(["pending", "accepted"])).first()
    if existing:
        raise ValueError("Friend request already exists")
    request = FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_incoming_requests(db: Session, user_id: str):
    return db.query(FriendRequest).filter(FriendRequest.to_user_id == user_id, FriendRequest.status == "pending").all()

def accept_friend_request(db: Session, request_id: str, user_id: str):
    request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.to_user_id == user_id,
        FriendRequest.status == "pending"
    ).first()
    if request:
        request.status = "accepted"
        db.commit()
        db.refresh(request)
        return request
    return None


def reject_friend_request(db: Session, request_id: str, user_id: str):
    request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.to_user_id == user_id,
        FriendRequest.status == "pending"
    ).first()
    if request:
        request.status = "rejected"
        db.commit()
        db.refresh(request)
        return request
    return None

def get_friends(db: Session, user_id: str):
    requests = db.query(FriendRequest).filter(
        ((FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id)) &
         (FriendRequest.status == "accepted")
    ).all()
    friend_ids = []
    for req in requests:
        if req.from_user_id == user_id:
            friend_ids.append(req.to_user_id)
        else:
            friend_ids.append(req.from_user_id)
    return db.query(User).filter(User.id.in_(friend_ids)).all()

def get_friend_habits(db: Session, user_id: str):
    requests = db.query(FriendRequest).filter(
        FriendRequest.status == "accepted",
        (FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id)
    ).all()
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
            result.append({"user" : user, "habit": habit})
        
    return result

// Habit Invitations

def create_habit_invitations(db: Session, habit_id: str, from_user_id: str, friend_ids: list[str]):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == from_user_id).first()
    if not habit:
        raise ValueError("Habit not found")

    created = []
    for friend_id in friend_ids:
        if friend_id == from_user_id:
            continue
        existing = db.query(HabitInvitation).filter(
            HabitInvitation.habit_id == habit_id,
            HabitInvitation.to_user_id == friend_id,
            HabitInvitation.status == "pending"
        ).first()
        if existing:
            continue
        invitation = HabitInvitation(
            habit_id=habit_id,
            from_user_id=from_user_id,
            to_user_id=friend_id
        )
        db.add(invitation)
        created.append(invitation)
    db.commit()
    for inv in created:
        db.refresh(inv)
    return created


def get_incoming_habit_invitations(db: Session, user_id: str):
    return db.query(HabitInvitation).filter(
        HabitInvitation.to_user_id == user_id,
        HabitInvitation.status == "pending"
    ).all()


def accept_habit_invitation(db: Session, invitation_id: str, user_id: str):
    invitation = db.query(HabitInvitation).filter(
        HabitInvitation.id == invitation_id,
        HabitInvitation.to_user_id == user_id,
        HabitInvitation.status == "pending"
    ).first()
    if not invitation:
        return None

    invitation.status = "accepted"

    # Copy the habit for the accepting user
    original_habit = db.query(Habit).filter(Habit.id == invitation.habit_id).first()
    if original_habit:
        new_habit = Habit(
            user_id=user_id,
            name=original_habit.name,
            days=original_habit.days,
            image=original_habit.image,
            is_small=original_habit.is_small,
        )
        db.add(new_habit)

    db.commit()
    db.refresh(invitation)
    return invitation


def reject_habit_invitation(db: Session, invitation_id: str, user_id: str):
    invitation = db.query(HabitInvitation).filter(
        HabitInvitation.id == invitation_id,
        HabitInvitation.to_user_id == user_id,
        HabitInvitation.status == "pending"
    ).first()
    if not invitation:
        return None

    invitation.status = "rejected"
    db.commit()
    db.refresh(invitation)
    return invitation

// Habit Completions

def create_completion(db: Session, habit_id: str, user_id: str, date: str):
    existing = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.user_id == user_id,
        HabitCompletion.date == date
    ).first()
    if existing:
        return existing

    completion = HabitCompletion(
        habit_id=habit_id,
        user_id=user_id,
        date=date
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion

def delete_completion(db: Session, habit_id: str, user_id: str, date: str):
    completion = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.user_id == user_id,
        HabitCompletion.date == date
    ).first()
    if completion:
        db.delete(completion)
        db.commit()
    return completion

def get_week_completions(db: Session, user_id: str, week_start: str):
    from datetime import datetime, timedelta
    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=7)
    end_str = end.strftime("%Y-%m-%d")

    return db.query(HabitCompletion).filter(
        HabitCompletion.user_id == user_id,
        HabitCompletion.date >= week_start,
        HabitCompletion.date < end_str
    ).all()

def get_habit_week_completion_count(db: Session, habit_id: str, user_id: str, week_start: str) -> int:
    from datetime import datetime, timedelta
    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=7)
    end_str = end.strftime("%Y-%m-%d")

    return db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.user_id == user_id,
        HabitCompletion.date >= week_start,
        HabitCompletion.date < end_str
    ).count()

def advance_habit(db: Session, habit_id: str, user_id: str):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user_id
    ).first()
    if not habit:
        return None

    habit.level += 1
    if habit.level > 3:
        habit.is_archived = True

    db.commit()
    db.refresh(habit)
    return habit

def reset_habit_level(db: Session, habit_id: str, user_id: str):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user_id
    ).first()
    if not habit:
        return None

    habit.level = 1
    db.commit()
    db.refresh(habit)
    return habit
