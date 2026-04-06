from pydantic import BaseModel
from datetime import datetime


class CourseRequest(BaseModel):
    title: str
    category: str
    description: str


class CourseUpdateRequest(BaseModel):
    title: str | None = None
    category: str | None = None
    description: str | None = None


class CourseResponse(BaseModel):
    id: int
    title: str
    category: str
    description: str
    image_path: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
