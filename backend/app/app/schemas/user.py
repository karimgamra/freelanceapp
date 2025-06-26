from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
import re

class CreateUser(BaseModel):
    name: str = Field(min_length=6)
    email: str
    password: str
    role: Literal["client", "freelance"] = Field(default="client")
    
    @field_validator("password")
    def password_validate(cls, v):
        if len(v) < 8:
            raise ValueError("Your Password Must Be At Least 8 Characters Long")
        return v
    
    @field_validator("email")
    def email_validate(cls, v):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v
    
    model_config = {
        "from_attributes": True
    }

class UserResponse(BaseModel):
    name: str
    email: str
    role: Literal["client", "freelance"]
    is_banned : bool
    
    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    password: str
    email: str
    
    @field_validator("email")
    def email_validate(cls, v):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v
    
    @field_validator("password")
    def password_validate(cls, v):
        if len(v) < 8:
            raise ValueError("Your Password Must Be At Least 8 Characters Long")
        return v
    
    model_config = {
        "from_attributes": True
    }

class UpdateUser(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Literal["client", "freelance"]] = None
    name: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }

class UpdatePassword(BaseModel):
    email: str
    
    @field_validator("email")
    def email_validate(cls, v):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v
    
    model_config = {
        "from_attributes": True
    }

class AdminUserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: Literal["client", "freelance"]
    is_banned: Optional[bool] = None  # Added if part of your User model
    
    model_config = {
        "from_attributes": True
    }