from pydantic import BaseModel, Field
from typing import List, Optional


class CreateProfile(BaseModel):
    bio: str = Field(
        min_length=10, description="A short biography or description of the user."
    )

    skills: List[str] = Field(min_items=1, description="A list of skills or expertise.")

    experience: Optional[str] = Field(
        default=None, description="Professional experience or background details."
    )

    hourly_rate: Optional[float] = Field(
        default=None, ge=0, description="Hourly rate for services, if applicable."
    )

    location: Optional[str] = Field(
        default=None, description="User's location, e.g., city or country."
    )

    available: Optional[bool] = Field(
        default=None, description="Availability status for work or projects."
    )


class UpdateProfile(BaseModel):
    bio: str = Field(
        min_length=10,
    )
    skills: List[str] = Field(min_items=1, description="A list of skills or expertise.")

    experience: Optional[str] = Field(
        default=None,
    )

    hourly_rate: Optional[float] = Field(
        default=None,
        ge=0,
    )

    location: Optional[str] = Field(
        default=None,
    )

    available: Optional[bool] = Field(
        default=None,
    )
    portfolio_links: Optional[str] = None
