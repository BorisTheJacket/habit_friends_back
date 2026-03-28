from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./habit_friends.db")

# Force IPv4 connection for psycopg2
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL += "&application_name=habit_friends"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
        }
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()