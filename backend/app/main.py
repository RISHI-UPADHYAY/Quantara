from fastapi import FastAPI

from app.database.session import Base, engine
from app.models.user import User
from app.api.v1.auth.register import router as register_router
from app.api.v1.auth.login import router as login_router
from app.api.v1.users.me import router as users_router
from app.api.v1.auth.refresh_token import router as refresh_router
from app.api.v1.auth.logout import router as logout_router
from app.api.v1.auth.logout_all import router as logout_all_router
from app.api.v1.auth.sessions import router as sessions_router
from app.api.v1.auth.revoke_session import router as revoke_session_router
from app.api.v1.auth.change_password import router as change_password_router
from app.api.v1.auth.forgot_password import router as forgot_password_router
from app.api.v1.auth.reset_password import router as reset_password_router
from app.api.v1.auth.verify_email import router as verify_email_router
from app.api.v1.users.list import router as users_list_router
from app.api.v1.users.update_role import router as update_role_router

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
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    logout_all_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    users_list_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    update_role_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    refresh_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    sessions_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    revoke_session_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    change_password_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    forgot_password_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    reset_password_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    verify_email_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

@app.get("/")
def root():
    return { "message": "Welcome to Quantara API" }