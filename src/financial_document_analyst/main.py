"""FastAPI application factory and default application instance."""

from fastapi import FastAPI

from financial_document_analyst.api.routes.documents import router as documents_router
from financial_document_analyst.api.routes.health import router as health_router
from financial_document_analyst.api.routes.queries import router as queries_router
from financial_document_analyst.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application instance with explicit, testable configuration."""

    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.app_debug,
        description="Financial document intelligence and RAG API.",
    )
    application.include_router(health_router)
    application.include_router(documents_router)
    application.include_router(queries_router)
    return application


app = create_app()
