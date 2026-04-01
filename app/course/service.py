import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.course.model import Course
from app.course.repository import CourseRepository
from app.course.schema import CourseRequest
from app.shared.exception import RecursoNaoEncontradoException, RegraDeNegocioException
from app.core.config import settings


class CourseService:
    def __init__(self, db: AsyncSession):
        self.repository = CourseRepository(db)

    async def criar(self, request: CourseRequest, imagem: UploadFile | None) -> Course:
        image_path = self._salvar_imagem(imagem) if imagem else None
        course = Course(
            title=request.title,
            category=request.category,
            description=request.description,
            image_path=image_path,
        )
        return await self.repository.save(course)

    async def listar(self) -> list[Course]:
        return await self.repository.find_all()

    async def buscar_por_id(self, course_id: int) -> Course:
        course = await self.repository.find_by_id(course_id)
        if not course:
            raise RecursoNaoEncontradoException(f"Curso {course_id} não encontrado")
        return course

    def _salvar_imagem(self, imagem: UploadFile) -> str:
        conteudo = imagem.file.read()
        if not conteudo[:4].startswith((b"\xff\xd8", b"\x89PNG", b"GIF8", b"RIFF", b"WEBP")):
            if not imagem.content_type or not imagem.content_type.startswith("image/"):
                raise RegraDeNegocioException("Arquivo enviado não é uma imagem válida")
        ext = os.path.splitext(imagem.filename)[-1] or ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "courses")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(conteudo)
        return filepath
