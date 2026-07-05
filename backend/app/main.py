from fastapi import FastAPI

from app.database.session import Base, engine
from app.models.user import User
from app.api.v1.auth.register import router as register_router


app = FastAPI(
    title = "Quantara API",
    version = "1.0.0"
)

app.include_router(
    register_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

@app.get("/")
def root():
    return { "message": "Welcome to Quantara API" }