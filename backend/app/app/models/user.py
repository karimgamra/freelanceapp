from sqlalchemy import UUID, Boolean, DateTime, Integer , String , Column
from ..db.database import Base
import uuid
from sqlalchemy.sql import func


class User (Base) :
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True , default=uuid.uuid4 , unique=True , nullable=False)
    name = Column(String , nullable=False)
    email = Column (String , nullable=False , unique=True)
    password  = Column (String , nullable=False)
    role = Column (String , nullable=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
