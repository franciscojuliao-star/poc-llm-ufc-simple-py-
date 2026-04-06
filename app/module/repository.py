from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.module.model import Module


class ModuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, module: Module) -> Module:
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def find_by_course(self, course_id: int) -> list[Module]:
        result = await self.db.execute(select(Module).where(Module.course_id == course_id))
        return list(result.scalars().all())

    async def find_by_id(self, module_id: int) -> Module | None:
        result = await self.db.execute(select(Module).where(Module.id == module_id))
        return result.scalar_one_or_none()

    async def count_by_course(self, course_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Module).where(Module.course_id == course_id)
        )
        return result.scalar() or 0

    async def delete(self, module: Module) -> None:
        await self.db.delete(module)
        await self.db.commit()
