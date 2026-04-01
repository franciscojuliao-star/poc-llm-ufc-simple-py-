from sqlalchemy.orm import Session
from app.course.model import Course


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, course: Course) -> Course:
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def find_all(self) -> list[Course]:
        return self.db.query(Course).all()

    def find_by_id(self, course_id: int) -> Course | None:
        return self.db.query(Course).filter(Course.id == course_id).first()
