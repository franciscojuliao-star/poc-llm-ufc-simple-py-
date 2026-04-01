from sqlalchemy.orm import Session
from app.module.model import Module


class ModuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, module: Module) -> Module:
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def find_by_course(self, course_id: int) -> list[Module]:
        return self.db.query(Module).filter(Module.course_id == course_id).all()

    def find_by_id(self, module_id: int) -> Module | None:
        return self.db.query(Module).filter(Module.id == module_id).first()

    def count_by_course(self, course_id: int) -> int:
        return self.db.query(Module).filter(Module.course_id == course_id).count()
