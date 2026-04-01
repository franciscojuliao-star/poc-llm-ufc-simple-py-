from sqlalchemy.orm import Session
from app.lesson.model import Lesson


class LessonRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, lesson: Lesson) -> Lesson:
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def find_by_module(self, module_id: int) -> list[Lesson]:
        return self.db.query(Lesson).filter(Lesson.module_id == module_id).all()

    def find_by_id(self, lesson_id: int) -> Lesson | None:
        return self.db.query(Lesson).filter(Lesson.id == lesson_id).first()

    def count_by_module(self, module_id: int) -> int:
        return self.db.query(Lesson).filter(Lesson.module_id == module_id).count()
