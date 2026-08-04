import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    password_hash:Mapped[str] = mapped_column(String(255))

    reset_password_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    reset_password_expire: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    email_verification_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    email_verification_expire: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )