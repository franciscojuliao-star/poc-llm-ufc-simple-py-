from pydantic import BaseModel
from datetime import datetime


class AlternativeRequest(BaseModel):
    text: str
    correct: bool = False


class AlternativeResponse(BaseModel):
    id: int
    text: str
    correct: bool

    model_config = {"from_attributes": True}


class QuestionRequest(BaseModel):
    statement: str
    points: int = 1
    alternatives: list[AlternativeRequest]


class QuestionResponse(BaseModel):
    id: int
    statement: str
    points: int
    order_num: int
    alternatives: list[AlternativeResponse]

    model_config = {"from_attributes": True}


class QuizRequest(BaseModel):
    questions: list[QuestionRequest]


class QuizConfigRequest(BaseModel):
    show_wrong_answers: bool = False
    show_correct_answers: bool = False
    show_points: bool = False


class QuizResponse(BaseModel):
    id: int
    module_id: int
    show_wrong_answers: bool
    show_correct_answers: bool
    show_points: bool
    questions: list[QuestionResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuizGeneratedAlternative(BaseModel):
    text: str
    correct: bool


class QuizGeneratedQuestion(BaseModel):
    statement: str
    points: int = 1
    order_num: int
    alternatives: list[QuizGeneratedAlternative]


class QuizGeneratedResponse(BaseModel):
    questions: list[QuizGeneratedQuestion]
