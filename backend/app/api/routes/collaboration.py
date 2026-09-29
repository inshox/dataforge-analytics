"""Collaboration layer — local-first workspaces (no cloud)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import WorkspaceResponse
from app.models.v12 import ActivityLogRecord, CommentRecord, TeamMemberRecord, WorkspaceRecord

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None


class CommentCreate(BaseModel):
    workspace_id: str
    target_type: str
    target_id: str
    body: str
    author: str = "Local User"


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(session: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await session.execute(select(WorkspaceRecord))).scalars().all()
    out: list[WorkspaceResponse] = []
    for ws in rows:
        members = (
            await session.execute(
                select(TeamMemberRecord).where(TeamMemberRecord.workspace_id == ws.id)
            )
        ).scalars().all()
        out.append(
            WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                members=[
                    {"id": m.id, "name": m.display_name, "role": m.role}
                    for m in members
                ],
            )
        )
    return out


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    body: WorkspaceCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    import uuid

    ws = WorkspaceRecord(id=str(uuid.uuid4()), name=body.name, description=body.description)
    session.add(ws)
    session.add(
        TeamMemberRecord(
            workspace_id=ws.id,
            display_name="Admin",
            role="admin",
        )
    )
    await session.commit()
    return WorkspaceResponse(id=ws.id, name=ws.name, description=ws.description, members=[])


@router.post("/comments")
async def add_comment(body: CommentCreate, session: Annotated[AsyncSession, Depends(get_db)]):
    import uuid

    c = CommentRecord(
        id=str(uuid.uuid4()),
        workspace_id=body.workspace_id,
        target_type=body.target_type,
        target_id=body.target_id,
        author=body.author,
        body=body.body,
    )
    session.add(c)
    session.add(
        ActivityLogRecord(
            workspace_id=body.workspace_id,
            action="comment_added",
            entity_type=body.target_type,
            entity_id=body.target_id,
        )
    )
    await session.commit()
    return {"id": c.id, "ok": True}


@router.get("/activity")
async def activity_log(
    session: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: str | None = None,
    limit: int = 50,
):
    q = select(ActivityLogRecord).order_by(ActivityLogRecord.created_at.desc()).limit(limit)
    if workspace_id:
        q = q.where(ActivityLogRecord.workspace_id == workspace_id)
    rows = (await session.execute(q)).scalars().all()
    return [
        {
            "id": r.id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
