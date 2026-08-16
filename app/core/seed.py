import uuid
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User
from app.models.taxonomy import University, Faculty, Department, Level, Subject
from app.models.enums import UserRole

def seed_data(db: Session):
    settings = get_settings()
    # 1. Default University (Legacy)
    uni_model = db.query(University).filter(University.name == "جامعة نموذجية").first()
    if not uni_model:
        uni_model = University(
            id=str(uuid.uuid4()),
            name="جامعة نموذجية",
            name_en="Model University",
            city="Sanaa",
            is_active=True
        )
        db.add(uni_model)
        db.flush()
    
    # 2. جامعة القلم (Requested)
    uni_qalam = db.query(University).filter(University.name == "جامعة القلم").first()
    if not uni_qalam:
        uni_qalam = University(
            id=str(uuid.uuid4()),
            name="جامعة القلم",
            name_en="Al-Qalam University",
            city="Ibb",
            is_active=True
        )
        db.add(uni_qalam)
        db.flush()
        print(f"Seeded University: {uni_qalam.name}")
    
    # 3. كلية الهندسة وتقنية المعلومات
    fac = db.query(Faculty).filter(Faculty.name == "كلية الهندسة وتقنية المعلومات", Faculty.university_id == uni_qalam.id).first()
    if not fac:
        fac = Faculty(
            id=str(uuid.uuid4()),
            university_id=uni_qalam.id,
            name="كلية الهندسة وتقنية المعلومات",
            name_en="Faculty of Engineering and IT",
            is_active=True
        )
        db.add(fac)
        db.flush()
    
    # 4. قسم تقنية المعلومات
    dept = db.query(Department).filter(Department.name == "قسم تقنية المعلومات", Department.faculty_id == fac.id).first()
    if not dept:
        dept = Department(
            id=str(uuid.uuid4()),
            university_id=uni_qalam.id,
            faculty_id=fac.id,
            name="قسم تقنية المعلومات",
            name_en="IT Department",
            is_active=True
        )
        db.add(dept)
        db.flush()
    
    # 5. المستوى الثالث - الترم الأول
    lvl = db.query(Level).filter(Level.name == "المستوى الثالث - الترم الأول", Level.department_id == dept.id).first()
    if not lvl:
        lvl = Level(
            id=str(uuid.uuid4()),
            university_id=uni_qalam.id,
            department_id=dept.id,
            name="المستوى الثالث - الترم الأول",
            name_en="Level 3 - Semester 1",
            order_index=3
        )
        db.add(lvl)
        db.flush()
    
    # 6. تحليل وتصميم نظم
    sub = db.query(Subject).filter(Subject.name == "تحليل وتصميم نظم", Subject.level_id == lvl.id).first()
    if not sub:
        sub = Subject(
            id=str(uuid.uuid4()),
            university_id=uni_qalam.id,
            level_id=lvl.id,
            name="تحليل وتصميم نظم",
            name_en="Systems Analysis and Design",
            code="SAD301"
        )
        db.add(sub)
        db.flush()

    # 7. Ensure Admin account exists
    admin_email = settings.INITIAL_ADMIN_EMAIL.strip()
    admin_password = settings.INITIAL_ADMIN_PASSWORD
    admin = db.query(User).filter(User.email == admin_email).first() if admin_email else None
    if admin_email and admin_password and not admin:
        admin = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            full_name="Administrator",
            password_hash=hash_password(admin_password),
            role=UserRole.ADMINISTRATOR,
            university_id=uni_qalam.id,
            is_active=True
        )
        db.add(admin)
    
    db.commit()
