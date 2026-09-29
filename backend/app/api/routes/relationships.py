"""Dataset relationships API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import RelationshipResponse, RelationshipSpec
from app.services.relationship_service import RelationshipService

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("", response_model=list[RelationshipResponse])
async def list_relationships(session: Annotated[AsyncSession, Depends(get_db)]):
    return await RelationshipService.list_relationships(session)


@router.get("/graph")
async def relationship_graph(session: Annotated[AsyncSession, Depends(get_db)]):
    return await RelationshipService.graph(session)


@router.post("/detect", response_model=list[RelationshipResponse])
async def detect_relationships(session: Annotated[AsyncSession, Depends(get_db)]):
    return await RelationshipService.detect_relationships(session)


@router.post("", response_model=RelationshipResponse)
async def create_relationship(body: RelationshipSpec, session: Annotated[AsyncSession, Depends(get_db)]):
    return await RelationshipService.create_relationship(session, body)


@router.delete("/{rel_id}")
async def delete_relationship(rel_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    if not await RelationshipService.delete_relationship(session, rel_id):
        raise HTTPException(404, "Relationship not found")
    return {"ok": True}
