from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    avatar = Column(String, nullable=True)
    hashed_password = Column(String)

class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True)
    days = Column(Integer)
    image = Column(String, nullable=True)
    is_small = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.utcnow)
    selected_days = Column(String, nullable=True)
    reminder_time = Column(String, nullable=True)
    is_reminding = Column(Boolean, default=False)
    level = Column(Integer, default=1)
    is_archived = Column(Boolean, default=False)
    requires_mutual_confirmation = Column(Boolean, default=False)
    mutual_group_id = Column(String, nullable=True, index=True)

    user = relationship("User")


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    from_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # "pending", "accepted", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class HabitInvitation(Base):
    __tablename__ = "habit_invitations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    habit_id = Column(String, ForeignKey("habits.id"), nullable=False)
    from_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # "pending", "accepted", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)

    habit = relationship("Habit")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    habit_id = Column(String, ForeignKey("habits.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    habit = relationship("Habit")
    user = relationship("User")

class MutualDayConfirmation(Base):
    __tablename__ = "mutual_day_confirmations"
    __table_args__ = (
        UniqueConstraint("mutual_group_id", "user_id", "date", name="uix_mutual_confirmation"),
    )

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    mutual_group_id = Column(String, nullable=False, index=True)
    date = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")