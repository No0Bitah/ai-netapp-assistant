from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from datetime import datetime



class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=72)
    role: str = "viewer"  # optional, defaults to viewer

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True  # Pydantic v2: read from ORM objects

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class OrgCreate(BaseModel):
    name: str = Field(
        ..., 
        min_length=3, 
        max_length=100)

class OrgOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2: read from ORM objects

class OrgAddMember(BaseModel):
    user_email: EmailStr

class OrgMemberOut(BaseModel):
    user_name: str

class ConnectionCreate(BaseModel):
    svm_name: str = Field(
        ...,
        min_length=3,
        max_length=35,
        description="The name of the Connection"
    )
    base_url: str = Field(
        ...,
        description="The management endpoint",
        examples=["https//:127.0.0.1"]
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=25,
        description="Service account username for the storage system"
    )
    password: str = Field(
        ...,
        min_length=8,
    )
    scope: Literal["admin",
                   "application",
                    "cloud",
                    "cluster",
                    "NAS",
                    "NDMP",
                    "NVMe",
                    "name-services",
                    "networking",
                    "object-store",
                    "SAN",
                    "SVM",
                    "security",
                    "snaplock",
                    "snapmirror",
                    "storage",
                    "support"] = Field(
        default="admin",
        description="Permission"


    )

class SVMCreateRequest(BaseModel):
    connection_id: int
    name: str
    snapshot_policy: str = "default"