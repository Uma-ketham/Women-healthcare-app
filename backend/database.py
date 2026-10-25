<<<<<<< HEAD
=======

>>>>>>> 889abf9 (backend)
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./herhealth.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

<<<<<<< HEAD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
=======
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

>>>>>>> 889abf9 (backend)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
