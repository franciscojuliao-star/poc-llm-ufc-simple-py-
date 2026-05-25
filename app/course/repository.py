from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.course.model import Course


class CourseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, course: Course) -> Course:
        self.db.add(course)
        await self.db.commit()
        return course

    async def find_all(self, page: int = 1, per_page: int = 20) -> list[Course]:
        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(Course).order_by(Course.created_at).offset(offset).limit(per_page)
        )
        return list(result.scalars().all())

    async def find_by_id(self, course_id: int) -> Course | None:
        result = await self.db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def delete(self, course: Course) -> None:
        await self.db.delete(course)
        await self.db.commit()
