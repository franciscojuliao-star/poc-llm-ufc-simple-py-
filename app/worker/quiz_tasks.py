import json
import re
from app.worker.celery_app import celery_app
from app.shared.redis_client import get_sync_redis
from app.core.config import settings
from openai import OpenAI

PENDING_TTL = 86400  # 24 horas


@celery_app.task(bind=True, name="quiz.gerar_quiz", max_retries=3, default_retry_delay=5)
def gerar_quiz_task(self, module_id: int, conteudo: str, quantidade: int) -> None:
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
                        f"Você é um especialista em educação. Com base no conteúdo abaixo, gere {quantidade} "
                        "perguntas de múltipla escolha com 4 alternativas cada. Exatamente 1 alternativa deve ser correta. "
                        "Retorne APENAS um JSON válido no formato:\n"
                        '{"questions": [{"statement": "...", "points": 1, "order_num": 1, '
                        '"alternatives": [{"text": "...", "correct": true/false}]}]}\n\n'
                        f"Conteúdo:\n{conteudo}"
                    ),
                }
            ],
        )
        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        texto = match.group(0) if match else raw
        json.loads(texto)  # valida antes de salvar

        redis = get_sync_redis()
        redis.setex(f"pending:quiz:{module_id}", PENDING_TTL, texto)
    except Exception as exc:
        raise self.retry(exc=exc)
