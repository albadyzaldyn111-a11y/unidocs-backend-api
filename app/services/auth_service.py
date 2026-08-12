from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.repositories.taxonomy_repository import TaxonomyRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.taxonomy = TaxonomyRepository(db)
        self.audit = AuditService(db)

    def register(self, email: str, password: str, full_name: str, university_id: str):
        if self.users.get_by_email(email):
            raise AppError("Email already registered", "EMAIL_TAKEN", 409)

        universities = {u.id for u in self.taxonomy.list_universities()}
        if university_id not in universities:
            raise AppError("Invalid university", "INVALID_UNIVERSITY", 422)

        user = self.users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.STUDENT,
            university_id=university_id,
            is_active=True,
        )
        self.audit.log(user.id, "CREATE_USER", "user", user.id, "self-registration")
        self.db.commit()
        return user

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AppError("Invalid credentials", "INVALID_CREDENTIALS", 401)
        if not user.is_active:
            raise AppError("Account is deactivated", "ACCOUNT_DISABLED", 403)

        token = create_access_token(user_id=user.id, role=user.role.value, university_id=user.university_id)
        return token
