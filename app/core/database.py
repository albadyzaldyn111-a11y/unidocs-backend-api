from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# For PostgreSQL on Render/Supabase, we might need to adjust pool settings
engine_kwargs = {
    "connect_args": connect_args,
    "future": True,
}

if not settings.DATABASE_URL.startswith("sqlite"):
    # Add pooling settings for production PostgreSQL
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    })

# Remove pgbouncer query param if present, as psycopg2 doesn't like it in the DSN
db_url = settings.DATABASE_URL
if "pgbouncer=true" in db_url:
    db_url = db_url.replace("pgbouncer=true", "").replace("??", "?").rstrip("?").rstrip("&")

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def ensure_schema() -> None:
    """Create tables and add the small set of backwards-compatible file columns.

    The original project did not ship migrations for the file metadata columns.
    This keeps existing free-tier SQLite deployments upgradeable while remaining
    harmless for a fresh database or a PostgreSQL deployment.
    """
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "files" not in tables:
        return

    existing = {column["name"] for column in inspector.get_columns("files")}
    statements: list[str] = []
    if "original_filename" not in existing:
        statements.append(
            "ALTER TABLE files ADD COLUMN original_filename VARCHAR(512) NOT NULL DEFAULT 'upload'"
        )
    if "mime_type" not in existing:
        statements.append(
            "ALTER TABLE files ADD COLUMN mime_type VARCHAR(255) NOT NULL DEFAULT 'application/octet-stream'"
        )
    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
