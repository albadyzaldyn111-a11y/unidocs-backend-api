from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User
from app.models.taxonomy import University
from app.models.enums import UserRole
import uuid

def seed_data(db: Session):
    # 1. Ensure Default University exists
    uni = db.query(University).filter(University.name == "جامعة نموذجية").first()
    if not uni:
        uni = University(
            id=str(uuid.uuid4()),
            name="جامعة نموذجية",
            name_en="Model University",
            city="Sanaa",
            is_active=True
        )
        db.add(uni)
        db.flush()
    
    # 2. Ensure Admin account exists
    admin = db.query(User).filter(User.email == "admin@unidocs.com").first()
    if not admin:
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@unidocs.com",
            full_name="Administrator",
            password_hash=hash_password("admin123456"),
            role=UserRole.ADMINISTRATOR,
            university_id=uni.id,
            is_active=True
        )
        db.add(admin)
    
    db.commit()
