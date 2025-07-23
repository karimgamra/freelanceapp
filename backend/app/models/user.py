from sqlalchemy import Boolean, DateTime, String, Column
from ..db.database import Base
from sqlalchemy.orm import relationship

import uuid
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "user"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )

    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    profile = relationship(
        "Profile",  # string form!
        back_populates="user",
        uselist=False,
        cascade="all, delete",
    )

    jobs = relationship(
        "Job",
        back_populates="user",
        cascade="all, delete-orphan",
    )
