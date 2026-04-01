from sqlalchemy.orm import Session
from app.quiz.model import Quiz, Question, Alternative


class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, quiz: Quiz) -> Quiz:
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def find_by_module(self, module_id: int) -> Quiz | None:
        return self.db.query(Quiz).filter(Quiz.module_id == module_id).first()

    def find_by_id(self, quiz_id: int) -> Quiz | None:
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, question: Question) -> Question:
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def find_by_quiz(self, quiz_id: int) -> list[Question]:
        return self.db.query(Question).filter(Question.quiz_id == quiz_id).all()

    def find_by_id(self, question_id: int) -> Question | None:
        return self.db.query(Question).filter(Question.id == question_id).first()

    def count_by_quiz(self, quiz_id: int) -> int:
        return self.db.query(Question).filter(Question.quiz_id == quiz_id).count()


class AlternativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, alternative: Alternative) -> Alternative:
        self.db.add(alternative)
        self.db.commit()
        self.db.refresh(alternative)
        return alternative

    def find_by_question(self, question_id: int) -> list[Alternative]:
        return self.db.query(Alternative).filter(Alternative.question_id == question_id).all()
