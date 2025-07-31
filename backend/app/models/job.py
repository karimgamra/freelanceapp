import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from ..db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), ForeignKey("user.id"), nullable=False)

    title = Column(String(100), nullable=False)
    job_description = Column(Text, nullable=False)
    location = Column(String(100), nullable=True)
    budget = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)

    job_type = Column(String(50), nullable=True)  # e.g. 'fixed', 'hourly'
    category = Column(String(100), nullable=True)
    status = Column(String(50), default="open")
    deadline = Column(DateTime, nullable=True)
    estimated_duration = Column(String(100), nullable=True)
    work_mode = Column(String(50), nullable=True)  # remote/on-site/hybrid
    visibility = Column(String(50), default="public")
    payment_status = Column(String(50), default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="jobs")
