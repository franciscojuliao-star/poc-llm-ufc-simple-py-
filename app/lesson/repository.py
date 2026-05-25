from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.lesson.model import Lesson


class LessonRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, lesson: Lesson) -> Lesson:
        self.db.add(lesson)
        await self.db.commit()
        return lesson

    async def find_by_module(self, module_id: int) -> list[Lesson]:
        result = await self.db.execute(select(Lesson).where(Lesson.module_id == module_id))
        return list(result.scalars().all())

    async def find_by_id(self, lesson_id: int) -> Lesson | None:
        result = await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        return result.scalar_one_or_none()

    async def count_by_module(self, module_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Lesson).where(Lesson.module_id == module_id)
        )
        return result.scalar() or 0

    async def delete(self, lesson: Lesson) -> None:
        await self.db.delete(lesson)
        await self.db.commit()
