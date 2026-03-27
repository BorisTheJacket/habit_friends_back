from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True)
    days = Column(Integer)
    image = Column(LargeBinary, nullable=True)  # Store image as binary data
    is_small = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")