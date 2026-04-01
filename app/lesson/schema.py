from pydantic import BaseModel
from datetime import datetime


class LessonRequest(BaseModel):
    name: str
    content_editor: str | None = None


class LessonResponse(BaseModel):
    id: int
    name: str
    order_num: int
    file_path: str | None
    file_type: str | None
    content_editor: str | None
    content_generated: str | None
    module_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
