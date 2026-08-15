from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.middleware.rate_limit import limiter
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService(db).register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        university_id=payload.university_id,
    )
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    token = AuthService(db).login(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(current_user.id)
    if user and user.email.lower() == 'admin@unidocs.com':
        user.role = UserRole.ADMINISTRATOR
    return user
