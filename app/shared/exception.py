from fastapi import Request
from fastapi.responses import JSONResponse
from app.shared.schema import ApiResponse


class RecursoNaoEncontradoException(Exception):
    def __init__(self, mensagem: str):
        self.mensagem = mensagem


class RegraDeNegocioException(Exception):
    def __init__(self, mensagem: str):
        self.mensagem = mensagem


async def recurso_nao_encontrado_handler(request: Request, exc: RecursoNaoEncontradoException):
    return JSONResponse(status_code=404, content=ApiResponse.erro(exc.mensagem).model_dump(mode="json"))


async def regra_de_negocio_handler(request: Request, exc: RegraDeNegocioException):
    return JSONResponse(status_code=422, content=ApiResponse.erro(exc.mensagem).model_dump(mode="json"))


async def erro_interno_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse.erro(f"Erro interno: {str(exc)}").model_dump(mode="json"),
    )
