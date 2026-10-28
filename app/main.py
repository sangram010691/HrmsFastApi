"""App entry point. API docs: http://localhost:8000/docs"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.settings import settings
from app.database import Base, engine
from app import models  # noqa: F401 - registers SQLAlchemy models
from app.routers import auth, patients, appointments, visits, billing, inventory, labs, beds, dashboard, ai

if len(settings.jwt_secret) < 32 or "CHANGE_THIS" in settings.jwt_secret:
    raise RuntimeError("Set a random JWT_SECRET (at least 32 characters) in backend/.env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Easy for practice. Production projects should use Alembic migrations instead.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Hospital ERP Practice API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[url.strip() for url in settings.cors_origins.split(",") if url.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

for router in [auth.router, patients.router, appointments.router, visits.router, billing.router,
               inventory.router, labs.router, beds.router, dashboard.router, ai.router]:
    app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
