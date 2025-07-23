from sqlalchemy import Boolean, Float, String, Column, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("user.id"), unique=True, nullable=False)

    bio = Column(Text, nullable=False)
    skills = Column(String(1000), nullable=False)
    experience = Column(String(100), nullable=False)
    portfolio_links = Column(String(100), nullable=True)
    hourly_rate = Column(Float, nullable=True)
    location = Column(String(100), nullable=True)
    available = Column(Boolean, default=True)

    user = relationship("User", back_populates="profile")
