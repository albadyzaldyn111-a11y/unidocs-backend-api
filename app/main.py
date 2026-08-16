from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import admin, auth, files, moderation, notifications, settings as settings_routes, taxonomy, upload, upload_requests, users
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.repositories.misc_repositories import SettingsRepository
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.rate_limit import limiter

settings = get_settings()


async def rate_limit_handler(request, exc):
    return await app_error_handler(request, AppError("Too many requests", "RATE_LIMITED", 429))


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
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def maintenance_guard(request: Request, call_next):
    path = request.url.path
    allowed_during_maintenance = path in {"/health", "/api/auth/login", "/api/settings/public"} or path.startswith("/api/admin")
    if not allowed_during_maintenance and path.startswith("/api"):
        try:
            with SessionLocal() as db:
                enabled = SettingsRepository(db).get("maintenance_mode").lower() == "true"
                message = SettingsRepository(db).get("maintenance_message")
            if enabled:
                return JSONResponse(status_code=503, content={"message": message, "code": "MAINTENANCE_MODE"})
        except Exception:
            # A database outage must be handled by the normal endpoint error path.
            pass
    return await call_next(request)

# Standard API routes
app.include_router(auth.router)
app.include_router(taxonomy.router)
app.include_router(files.router, prefix="/api/files")
app.include_router(upload.router, prefix="/api")
app.include_router(upload_requests.router)
app.include_router(notifications.router)
app.include_router(moderation.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(settings_routes.router)

# Legacy compatibility for apps missing the /api prefix (specifically for upload/files)
app.include_router(files.router, prefix="/files", tags=["legacy"])
app.include_router(upload.router, prefix="", tags=["legacy"])


@app.on_event("startup")
def on_startup():
    # In production, use Alembic migrations instead of create_all.
    if settings.ENV == "development":
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"success": True, "message": "UniDocs API is running"}
