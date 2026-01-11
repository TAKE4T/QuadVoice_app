from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class IdentityDocType(str, Enum):
    skill = "skill"
    goal = "goal"
    knowledge = "knowledge"


class PlatformName(str, Enum):
    qiita = "qiita"
    zenn = "zenn"
    note = "note"
    owned = "owned"


class ProjectStatus(str, Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


@dataclass
class IdentityDoc:
    id: str
    type: IdentityDocType
    content: str
    embedding: List[float] = field(default_factory=list)
    user_id: Optional[str] = None


@dataclass
class PlatformStyle:
    id: str
    platform: PlatformName
    rules: Dict[str, str]
    version: int = 1
    user_id: Optional[str] = None


@dataclass
class WorkflowEvent:
    node: str
    message: str
    status: ProjectStatus


@dataclass
class ProjectResult:
    id: str
    theme: str
    status: ProjectStatus
    outputs: Dict[str, str] = field(default_factory=dict)
    events: List[WorkflowEvent] = field(default_factory=list)


def new_id() -> str:
    return str(uuid.uuid4())
