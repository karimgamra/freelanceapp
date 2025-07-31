from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class CreateJob(BaseModel):

    title: str
    job_description: str
    location: Optional[str]
    budget: Optional[float]
    is_active: Optional[bool] = True

    job_type: str
    category: str
    status: Optional[str] = "open"
    deadline: Optional[datetime] = None
    estimated_duration: Optional[str] = None
    work_mode: Optional[str] = None
    visibility: Optional[str] = "public"
    payment_status: Optional[str] = "pending"


class UpdateJob(BaseModel):
    title: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[int] = None
    is_active: Optional[bool] = None


class JobResponse(BaseModel):
    title: str
    job_description: str
    location: str
    budget: float

    class Config:
        from_attributes = True
