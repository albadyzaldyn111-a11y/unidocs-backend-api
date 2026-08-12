import io
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_unidocs.db"
os.environ["SECRET_KEY"] = "test_secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.taxonomy import Level, Department, Faculty, Subject, University

TEST_DB_URL = "sqlite:///./test_unidocs.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def seed_taxonomy(db_session):
    def _seed(name="Uni A"):
        uni = University(name=name, name_en=name, city="City")
        db_session.add(uni)
        db_session.flush()
        faculty = Faculty(university_id=uni.id, name="Faculty", name_en="Faculty")
        db_session.add(faculty)
        db_session.flush()
        dept = Department(university_id=uni.id, faculty_id=faculty.id, name="Dept", name_en="Dept")
        db_session.add(dept)
        db_session.flush()
        level = Level(university_id=uni.id, department_id=dept.id, name="Level 1", name_en="Level 1", order_index=1)
        db_session.add(level)
        db_session.flush()
        subject = Subject(university_id=uni.id, level_id=level.id, name="Subject", name_en="Subject", code="SUB101")
        db_session.add(subject)
        db_session.commit()
        return {"university": uni, "subject": subject}

    return _seed


def make_pdf_bytes(content: bytes = b"fake pdf body") -> bytes:
    return b"%PDF-1.4\n" + content
