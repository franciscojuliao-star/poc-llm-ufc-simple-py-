from app.worker.celery_app import celery_app
from app.shared.redis_client import get_sync_redis
from app.core.config import settings
from openai import OpenAI

PENDING_TTL = 86400  # 24 horas


@celery_app.task(bind=True, name="lesson.gerar_conteudo", max_retries=3, default_retry_delay=5)
def gerar_conteudo_task(self, lesson_id: int, fonte: str) -> None:
    try:
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
        redis = get_sync_redis()
        redis.setex(f"pending:lesson:{lesson_id}", PENDING_TTL, conteudo)
    except Exception as exc:
        raise self.retry(exc=exc)
