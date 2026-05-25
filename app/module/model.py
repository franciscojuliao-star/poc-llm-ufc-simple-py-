from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course: Mapped["Course"] = relationship(back_populates="modules")  # noqa: F821
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="module", cascade="all, delete-orphan")  # noqa: F821
    quiz: Mapped["Quiz | None"] = relationship(back_populates="module", cascade="all, delete-orphan", uselist=False)  # noqa: F821
