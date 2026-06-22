from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

def configure_error_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "erro": True,
                "mensagem": exc.detail,
                "detalhes": None
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "erro": True,
                "mensagem": "Os dados enviados são inválidos. Verifique as informações e tente novamente.",
                "detalhes": [{"campo": err["loc"][-1], "erro": err["msg"]} for err in exc.errors()]
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "erro": True,
                "mensagem": "Ocorreu um problema ao acessar o banco de dados. Tente novamente mais tarde.",
                "detalhes": None
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "erro": True,
                "mensagem": "Ops! Algo deu errado em nossos servidores. Já estamos trabalhando para resolver.",
                "detalhes": None
            }
        )
