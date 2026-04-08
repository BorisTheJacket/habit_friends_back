from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from database import engine
from models import Base
from routers import habits, users, friends

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Habit Friends Backend", version="1.0.0")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(habits.router, prefix="/habits", tags=["habits"])
app.include_router(friends.router, prefix="/friends", tags=["friends"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Habit Friends Backend"}