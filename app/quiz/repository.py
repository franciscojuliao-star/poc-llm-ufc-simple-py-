from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.quiz.model import Quiz, Question, Alternative


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, quiz: Quiz) -> Quiz:
        self.db.add(quiz)
        await self.db.commit()
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.id == quiz.id)
            .options(selectinload(Quiz.questions).selectinload(Question.alternatives))
        )
        return result.scalar_one()

    async def find_by_module(self, module_id: int) -> Quiz | None:
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.module_id == module_id)
            .options(selectinload(Quiz.questions).selectinload(Question.alternatives))
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, quiz_id: int) -> Quiz | None:
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions).selectinload(Question.alternatives))
        )
        return result.scalar_one_or_none()


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, question: Question) -> Question:
        self.db.add(question)
        await self.db.commit()
        result = await self.db.execute(
            select(Question)
            .where(Question.id == question.id)
            .options(selectinload(Question.alternatives))
        )
        return result.scalar_one()

    async def find_by_quiz(self, quiz_id: int) -> list[Question]:
        result = await self.db.execute(
            select(Question)
            .where(Question.quiz_id == quiz_id)
            .options(selectinload(Question.alternatives))
        )
        return list(result.scalars().all())

    async def find_by_id(self, question_id: int) -> Question | None:
        result = await self.db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def count_by_quiz(self, quiz_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Question).where(Question.quiz_id == quiz_id)
        )
        return result.scalar() or 0


class AlternativeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, alternative: Alternative) -> Alternative:
        self.db.add(alternative)
        await self.db.commit()
        await self.db.refresh(alternative)
        return alternative

    async def find_by_question(self, question_id: int) -> list[Alternative]:
        result = await self.db.execute(
            select(Alternative).where(Alternative.question_id == question_id)
        )
        return list(result.scalars().all())
