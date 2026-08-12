from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import admin, auth, files, moderation, notifications, taxonomy, upload, upload_requests, users
from app.core.config import get_settings
<<<<<<< HEAD
from app.core.database import Base, engine
=======
from app.core.database import ensure_schema
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.rate_limit import limiter

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, lambda r, e: app_error_handler(r, AppError("Too many requests", "RATE_LIMITED", 429)))
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth.router)
app.include_router(taxonomy.router)
app.include_router(files.router)
app.include_router(upload.router)
app.include_router(upload_requests.router)
app.include_router(notifications.router)
app.include_router(moderation.router)
app.include_router(admin.router)
app.include_router(users.router)


@app.on_event("startup")
def on_startup():
<<<<<<< HEAD
    # In production, use Alembic migrations instead of create_all.
    if settings.ENV == "development":
        Base.metadata.create_all(bind=engine)
=======
    ensure_schema()
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)


@app.get("/health")
def health():
    return {"success": True, "message": "UniDocs API is running"}
