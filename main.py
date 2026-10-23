
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from database import create_tables, get_db
from models import User
from security import hash_password, verify_password
from documents import router as documents_router

load_dotenv()

SECRET_KEY = os.getenv("TRUSTVAULT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "TRUSTVAULT_SECRET_KEY is missing. Add it to your .env file."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="TrustVault",
    description="Secure document sharing with an audit trail",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(documents_router)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="trustvault_session",
    max_age=3600,
    same_site="lax",
    https_only=os.getenv("TRUSTVAULT_HTTPS", "false").lower() == "true",
)


class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=12, max_length=128)


class LoginInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)


def public_user(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


@app.get("/")
def home():
    return {
        "message": "Welcome to TrustVault",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterInput,
    db: Session = Depends(get_db),
):
    username = data.username.strip().lower()

    if not username:
        raise HTTPException(status_code=400, detail="Invalid username")

    existing_user = db.scalar(
        select(User).where(User.username == username)
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="Username unavailable")

    user = User(
        username=username,
        password_hash=hash_password(data.password),
        role="viewer",
    )

    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Username unavailable"
        )

    return public_user(user)


@app.post("/login")
def login(
    data: LoginInput,
    request: Request,
    db: Session = Depends(get_db),
):
    username = data.username.strip().lower()
    user = db.scalar(select(User).where(User.username == username))

    if (
        user is None
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    request.session.clear()
    request.session["user_id"] = user.id

    return {"message": "Login successful", "user": public_user(user)}


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


@app.get("/me")
def me(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Please log in")

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Please log in")

    return public_user(user)
