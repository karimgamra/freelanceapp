from sqlalchemy import Text, String, Column, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from ..db.database import Base


class Job(Base):
    __tablenname__ = "job"

    id = Column(String(100), primary_key=True, default=lambda: (uuid.uuid4()))
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, unique=True)
    job_descreption = Column(Text, nullable=False)
    locaion = Column(String(40), nullable=False)

    user = relationship("User", back_populates="job")
