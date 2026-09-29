"""Transformation pipeline API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    TransformPipelineCreate,
    TransformPipelineResponse,
    TransformPreviewRequest,
    TransformPreviewResponse,
)
from app.services.dataset_service import DatasetService
from app.services.transformation_service import TransformationService

router = APIRouter(prefix="/datasets", tags=["transforms"])


@router.post("/{dataset_id}/transform/preview", response_model=TransformPreviewResponse)
async def transform_preview(dataset_id: str, body: TransformPreviewRequest):
    try:
        return TransformationService.preview(dataset_id, body)
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@router.get("/{dataset_id}/transform/pipelines", response_model=list[TransformPipelineResponse])
async def list_pipelines(
    dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]
):
    return await TransformationService.list_pipelines(session, dataset_id)


@router.post("/{dataset_id}/transform/pipelines", response_model=TransformPipelineResponse)
async def save_pipeline(
    dataset_id: str,
    body: TransformPipelineCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    return await TransformationService.save_pipeline(session, dataset_id, body)


@router.post("/{dataset_id}/transform/pipelines/{pipeline_id}/run")
async def run_pipeline(
    dataset_id: str,
    pipeline_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await TransformationService.run_pipeline(session, dataset_id, pipeline_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
