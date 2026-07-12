from fastapi import FastAPI

from app.database.session import Base, engine
from app.models.user import User
from app.api.v1.auth.register import router as register_router
from app.api.v1.auth.login import router as login_router
from app.api.v1.users.me import router as users_router
from app.api.v1.auth.refresh_token import router as refresh_router
from app.api.v1.auth.logout import router as logout_router


app = FastAPI(
    title = "Quantara API",
    version = "1.0.0"
)

app.include_router(
    register_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    login_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    logout_router,
    prefix="/api/v1/logout",
    tags=["Authentication"],
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    refresh_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

@app.get("/")
def root():
    return { "message": "Welcome to Quantara API" }