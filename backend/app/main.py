"""FastAPI application factory and entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import __version__
from app.api.v1 import api_v1
from app.core.bootstrap import ensure_admin_user
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db import engine
from app.services.gigachat import get_gigachat
from app.services.qdrant_service import get_qdrant

configure_logging()
log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown hooks once per process."""
    log.info(f"Starting {settings.app_name} v{__version__} (env={settings.app_env})")

    # Bootstrap admin (no-op if already exists)
    try:
        await ensure_admin_user()
    except Exception as e:  # noqa: BLE001
        log.error(f"Admin bootstrap failed: {e}")

    # Touch Qdrant so the collection is created on first request
    try:
        await get_qdrant()
        log.info(f"Qdrant collection '{settings.qdrant_collection}' is ready")
    except Exception as e:  # noqa: BLE001
        log.warning(f"Qdrant initialisation deferred (will retry on demand): {e}")

    yield

    log.info("Shutting down")
    try:
        await get_gigachat().close()
    except Exception as e:  # noqa: BLE001
        log.debug(f"GigaChat client close: {e}")
    try:
        qdrant = await get_qdrant()
        await qdrant.close()
    except Exception as e:  # noqa: BLE001
        log.debug(f"Qdrant client close: {e}")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Веб-сервис для оказания консультационных услуг "
            "сельхозпроизводителям по мерам государственной поддержки. "
            "RAG-система на базе GigaChat и Qdrant."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["meta"])
    async def health():
        """Liveness + dependency check."""
        result = {"status": "ok", "version": __version__, "checks": {}}
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            result["checks"]["database"] = "ok"
        except Exception as e:  # noqa: BLE001
            result["checks"]["database"] = f"error: {e}"
            result["status"] = "degraded"
        return result

    app.include_router(api_v1)
    return app


app = create_app()
