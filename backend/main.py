<<<<<<< HEAD
=======

>>>>>>> 889abf9 (backend)
import os
import json
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# ---------- Configuration ----------

SECRET_KEY = os.getenv("HERHEALTH_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "demo-only-change-this-secret-before-deployment"

DATABASE_URL = "sqlite:///./herhealth.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
password_hasher = PasswordHash.recommended()
security = HTTPBearer()

app = FastAPI(title="HerHealth API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Database tables ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    record_type = Column(String(20), nullable=False)
    record_data = Column(Text, nullable=False)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    email = Column(String(255), nullable=True)
    preferred = Column(String(50), nullable=True)


# Create tables only after all models are defined.
Base.metadata.create_all(bind=engine)


# ---------- Request models ----------

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RecordRequest(BaseModel):
    data: dict


class ProfileRequest(BaseModel):
    name: str = Field(default="", max_length=100)
    age: int | None = Field(default=None, ge=1, le=120)
    email: str | None = Field(default=None, max_length=255)
    preferred: str | None = Field(default=None, max_length=50)


# ---------- Database session ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Authentication ----------

def create_token(user_id: int) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(hours=8)

    return jwt.encode(
        {"sub": str(user_id), "exp": expiry},
        SECRET_KEY,
        algorithm="HS256",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Account not found",
        )

    return user


# ---------- Home ----------

@app.get("/")
def home():
    return {"message": "HerHealth API is running"}


# ---------- Register ----------

@app.post("/auth/register", status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    username = request.username.strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must have at least 3 characters",
        )

    existing = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    user = User(
        username=username,
        email=request.email.strip() if request.email else None,
        password_hash=password_hasher.hash(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Account created successfully",
        "username": user.username,
    }


# ---------- Login ----------

@app.post("/auth/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.username == request.username.strip())
        .first()
    )

    if not user or not password_hasher.verify(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    return {
        "access_token": create_token(user.id),
        "token_type": "bearer",
        "username": user.username,
    }


# ---------- User profile ----------

@app.get("/profile")
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user.id)
        .first()
    )

    if not profile:
        return {
            "name": user.username,
            "age": None,
            "email": user.email,
            "preferred": None,
        }

    return {
        "name": profile.name or user.username,
        "age": profile.age,
        "email": profile.email or user.email,
        "preferred": profile.preferred,
    }


@app.put("/profile")
def update_profile(
    request: ProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user.id)
        .first()
    )

    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)

    profile.name = request.name.strip() or user.username
    profile.age = request.age

    profile.email = (
        request.email.strip()
        if request.email and request.email.strip()
        else None
    )

    profile.preferred = (
        request.preferred.strip()
        if request.preferred and request.preferred.strip()
        else None
    )

    db.commit()
    db.refresh(profile)

    return {
        "message": "Profile saved successfully",
        "profile": {
            "name": profile.name,
            "age": profile.age,
            "email": profile.email,
            "preferred": profile.preferred,
        },
    }


# ---------- Save health records ----------

@app.post("/records/{record_type}", status_code=201)
def save_record(
    record_type: str,
    request: RecordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if record_type not in ("period", "symptom"):
        raise HTTPException(
            status_code=400,
            detail="Use period or symptom",
        )

    record = HealthRecord(
        user_id=user.id,
        record_type=record_type,
        record_data=json.dumps(request.data),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "type": record.record_type,
        "data": request.data,
    }


# ---------- Get all health records ----------

@app.get("/records")
def get_records(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user.id)
        .order_by(HealthRecord.id.desc())
        .all()
    )

    return [
        {
            "id": record.id,
            "type": record.record_type,
            "data": json.loads(record.record_data),
        }
        for record in records
    ]


# ---------- Get records by type ----------

@app.get("/records/{record_type}")
def get_records_by_type(
    record_type: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if record_type not in ("period", "symptom"):
        raise HTTPException(
            status_code=400,
            detail="Use period or symptom",
        )

    records = (
        db.query(HealthRecord)
        .filter(
            HealthRecord.user_id == user.id,
            HealthRecord.record_type == record_type,
        )
        .order_by(HealthRecord.id.desc())
        .all()
    )

    return [
        {
            "id": record.id,
            "type": record.record_type,
            "data": json.loads(record.record_data),
        }
        for record in records
    ]
