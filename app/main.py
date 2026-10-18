from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.database import Base, engine
from app.routers import auth, bookings, classes

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="StarLabs Fitness Studio Booking API",
    description=(
        "Sign up, log in, create and list classes, book slots, view your bookings. "
        "Class times are stored in IST."
    ),
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(bookings.router)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}