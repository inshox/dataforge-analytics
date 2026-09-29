"""FastAPI application entrypoint."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.__version__ import __version__
from app.api.routes import (
    chart_studio,
    charts,
    collaboration,
    dashboards,
    datasets,
    transforms,
    health,
    relationships,
    sql_studio,
    system,
    workers,
)
from app.core.config import ensure_data_dirs, get_settings
from app.core.database import async_session, init_db
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging_config import setup_logging
from app.services.demo_service import DemoService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.port import ensure_port_env, write_port_file

    if data_dir := os.environ.get("DATAFORGE_DATA_DIR"):
        settings = get_settings()
        settings.data_dir = settings.data_dir.__class__(data_dir)
    if db_url := os.environ.get("DATABASE_URL"):
        settings = get_settings()
        settings.database_url = db_url

    ensure_port_env()
    get_settings.cache_clear()
    settings = get_settings()
    data_path = ensure_data_dirs(settings)
    write_port_file(data_path, settings.port)
    log_file = setup_logging(data_path)
    logger.info("DataForge API %s starting — data_dir=%s log=%s", __version__, data_path, log_file)

    await init_db()
    async with async_session() as session:
        from sqlalchemy import func, select

        from app.models.dataset import DatasetRecord
        from app.models.enterprise import DashboardRecord

        demo = await DemoService.seed_if_empty(session)
        dash_count = await session.scalar(select(func.count()).select_from(DashboardRecord))
        if not dash_count:
            ds_id = demo.id if demo else "00000000-0000-4000-8000-000000000001"
            rec = await session.get(DatasetRecord, ds_id)
            if rec and rec.status == "ready":
                await DemoService.seed_demo_dashboard(session, rec.id)

    logger.info("DataForge API ready on %s:%s", settings.host, settings.port)
    yield
    logger.info("DataForge API shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins + ["*"] if settings.debug else settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(system.router, prefix=settings.api_prefix)
    app.include_router(datasets.router, prefix=settings.api_prefix)
    app.include_router(transforms.router, prefix=settings.api_prefix)
    app.include_router(dashboards.router, prefix=settings.api_prefix)
    app.include_router(chart_studio.router, prefix=settings.api_prefix)
    app.include_router(relationships.router, prefix=settings.api_prefix)
    app.include_router(sql_studio.router, prefix=settings.api_prefix)
    app.include_router(charts.router, prefix=settings.api_prefix)
    app.include_router(workers.router, prefix=settings.api_prefix)
    app.include_router(collaboration.router, prefix=settings.api_prefix)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    from app.core.port import ensure_port_env

    port = ensure_port_env()
    get_settings.cache_clear()
    s = get_settings()
    uvicorn.run("app.main:app", host=s.host, port=port, reload=s.debug)
