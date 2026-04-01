from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ApiResponse(BaseModel):
    sucesso: bool
    mensagem: str
    dados: Any = None
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now()
        super().__init__(**data)

    @classmethod
    def ok(cls, mensagem: str = "", dados: Any = None) -> "ApiResponse":
        return cls(sucesso=True, mensagem=mensagem, dados=dados)

    @classmethod
    def erro(cls, mensagem: str) -> "ApiResponse":
        return cls(sucesso=False, mensagem=mensagem, dados=None)
