import pdfplumber
from openai import OpenAI
from sqlalchemy.orm import Session
from app.lesson.model import Lesson
from app.lesson.schema import LessonResponse
from app.lesson.service import LessonService
from app.shared.exception import RegraDeNegocioException
from app.core.config import settings

_pending_content: dict[int, str] = {}


class LessonAiService:
    def __init__(self, db: Session):
        self.lesson_service = LessonService(db)
        self._pending = _pending_content

    def gerar_conteudo(self, lesson_id: int) -> str:
        lesson = self.lesson_service.buscar_entidade(lesson_id)
        fonte = self._extrair_fonte(lesson)
        if not fonte or not fonte.strip():
            raise RegraDeNegocioException("A aula não possui conteúdo legível para gerar via IA")

        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Você é um especialista em educação online. A partir do conteúdo abaixo, "
                        "gere um conteúdo de aula formatado em HTML semântico, bem estruturado, "
                        "com títulos (h2, h3), parágrafos, listas e destaques onde apropriado. "
                        "Retorne apenas o HTML sem delimitadores de código.\n\nConteúdo:\n" + fonte
                    ),
                }
            ],
        )
        conteudo = response.choices[0].message.content
        self._pending[lesson_id] = conteudo
        return conteudo

    def buscar_conteudo_pendente(self, lesson_id: int) -> str:
        pendente = self._pending.get(lesson_id)
        if not pendente:
            raise RegraDeNegocioException("Nenhum conteúdo pendente para esta aula")
        return pendente

    def confirmar_conteudo(self, lesson_id: int) -> LessonResponse:
        pendente = self.buscar_conteudo_pendente(lesson_id)
        lesson = self.lesson_service.buscar_entidade(lesson_id)
        lesson.content_editor = pendente
        self.lesson_service.salvar_conteudo_gerado(lesson)
        del self._pending[lesson_id]
        return LessonResponse.model_validate(lesson)

    def _extrair_fonte(self, lesson: Lesson) -> str | None:
        if lesson.file_path and lesson.file_type == "PDF":
            return self._extrair_texto_pdf(lesson.file_path)
        return lesson.content_editor

    def _extrair_texto_pdf(self, file_path: str) -> str:
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
