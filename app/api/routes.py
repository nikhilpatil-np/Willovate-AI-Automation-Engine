"""
API Routes — Router registration
==================================
Registers the NL pipeline router onto the main FastAPI app so all
endpoints appear in the Swagger UI at /docs.
"""

from fastapi import FastAPI
from app.api.nl_pipeline import router as pipeline_router


def register_routes(main_app: FastAPI) -> None:
    """
    Include the pipeline router with prefix /api/v1.

    All endpoints become visible in the main Swagger UI at /docs:
      POST /api/v1/generate-workflow
      POST /api/v1/execute
      POST /api/v1/normalize
      POST /api/v1/detect-intent
      POST /api/v1/multi-step-plan
      GET  /api/v1/health
    """

    main_app.include_router(pipeline_router, prefix="/api/v1")
