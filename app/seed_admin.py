"""
Usage:
    python -m app.seed_admin

Creates one University and one Administrator account using values from
environment variables. Never commit real credentials — set
INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD in your local .env or shell.
"""
import getpass
import sys

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.taxonomy import University
from app.models.user import User


def main():
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == UserRole.ADMINISTRATOR).first()
        if existing_admin:
            print(f"An administrator already exists: {existing_admin.email}")
            return

        university = db.query(University).first()
        if not university:
            university = University(name="الجامعة الافتراضية", name_en="Default University", city="—")
            db.add(university)
            db.flush()

        email = settings.INITIAL_ADMIN_EMAIL or input("Admin email: ")
        password = settings.INITIAL_ADMIN_PASSWORD or getpass.getpass("Admin password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            sys.exit(1)

        admin = User(
            email=email,
            password_hash=hash_password(password),
            full_name="System Administrator",
            role=UserRole.ADMINISTRATOR,
            university_id=university.id,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Administrator created: {email} (university_id={university.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
