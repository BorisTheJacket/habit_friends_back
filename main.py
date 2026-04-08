from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Response
from database import engine
from models import Base
from routers import habits, users, friends

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Habit Friends Backend", version="1.0.0")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(habits.router, prefix="/habits", tags=["habits"])
app.include_router(friends.router, prefix="/friends", tags=["friends"])

SUSPICIOUS_PATHS = [".env", ".git", "wp-config.php", "phpinfo.php", "debugbar"]

@app.middleware("http")
async def block_scanners(request: Request, call_next):
    path = request.url.path
    if any(bad in path for bad in SUSPICIOUS_PATHS):
        return Response(status_code=403)
    return await call_next(request)


@app.get("/")
def read_root():
    return {"message": "Welcome to Habit Friends Backend"}