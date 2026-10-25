<<<<<<< HEAD
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    email = Column(String(255), nullable=True)
    preferred = Column(String(50), nullable=True)


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    record_type = Column(String(20), nullable=False)
    record_data = Column(Text, nullable=False)
=======

from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from database import Base


class Period(Base):
    __tablename__ = "periods"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    cycle_length = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    severity = Column(Integer, nullable=False, default=1)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
>>>>>>> 889abf9 (backend)
