from pydantic import BaseModel
from datetime import datetime


class ModuleRequest(BaseModel):
    name: str


class ModuleUpdateRequest(BaseModel):
    name: str | None = None


class ModuleResponse(BaseModel):
    id: int
    name: str
    order_num: int
    image_path: str | None
    course_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
