from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.domain import IdentityDocType, PlatformName, ProjectStatus, WorkflowEvent


class IdentityIngestResponse(BaseModel):
    count: int
    doc_ids: List[str]
    note: str = "stored in memory for now"


class StyleIngestResponse(BaseModel):
    platform: PlatformName
    version: int
    summary: Dict[str, str]


class GenerateRequest(BaseModel):
    theme: str = Field(..., description="central topic for the four outputs")


class GenerateResponse(BaseModel):
    project_id: str
    status: ProjectStatus
    preview: Dict[str, str]


class WorkflowEventResponse(BaseModel):
    node: str
    message: str
    status: ProjectStatus

    @classmethod
    def from_domain(cls, event: WorkflowEvent) -> "WorkflowEventResponse":
        return cls(node=event.node, message=event.message, status=event.status)


class ProjectResultResponse(BaseModel):
    project_id: str
    theme: str
    status: ProjectStatus
    outputs: Dict[str, str]
    events: List[WorkflowEventResponse]
