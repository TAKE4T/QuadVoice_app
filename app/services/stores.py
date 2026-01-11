from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.models.domain import IdentityDoc, IdentityDocType, PlatformName, PlatformStyle, ProjectResult, ProjectStatus, WorkflowEvent, new_id
from app.services.supabase_client import fetch_project, get_supabase_client, insert, upsert, update_project


logger = logging.getLogger(__name__)


class DataStore:
    """Supabase-backed store with in-memory fallback for development."""

    def __init__(self) -> None:
        self.client = get_supabase_client()
        self._docs: Dict[str, IdentityDoc] = {}
        self._styles: Dict[PlatformName, PlatformStyle] = {}
        self._projects: Dict[str, ProjectResult] = {}
        self._hydrate()

    # Identity docs
    def save_identity(self, doc_type: IdentityDocType, content: str, embedding: List[float], user_id: Optional[str] = None) -> IdentityDoc:
        doc = IdentityDoc(id=new_id(), type=doc_type, content=content, embedding=embedding, user_id=user_id)
        payload = {
            "id": doc.id,
            "user_id": user_id,
            "type": doc_type.value,
            "content": content,
            "embedding": embedding,
        }
        upsert("Identity_Docs", payload, self.client)
        self._docs[doc.id] = doc
        return doc

    def list_identity_contents(self) -> List[str]:
        return [doc.content for doc in self._docs.values()]

    # Platform styles
    def save_style(self, platform: PlatformName, rules: Dict[str, str], user_id: Optional[str] = None) -> PlatformStyle:
        current_version = self._styles.get(platform).version if platform in self._styles else 0
        style = PlatformStyle(id=new_id(), platform=platform, rules=rules, version=current_version + 1, user_id=user_id)
        payload = {
            "id": style.id,
            "user_id": user_id,
            "platform": platform.value,
            "rules": rules,
            "version": style.version,
        }
        upsert("Platform_Styles", payload, self.client)
        self._styles[platform] = style
        return style

    def get_style(self, platform: PlatformName) -> PlatformStyle | None:
        return self._styles.get(platform)

    # Projects
    def create_project(self, theme: str) -> ProjectResult:
        project = ProjectResult(id=new_id(), theme=theme, status=ProjectStatus.processing)
        payload = {"id": project.id, "theme": theme, "status": project.status.value, "result_json": {}, "events": []}
        insert("Projects", payload, self.client)
        self._projects[project.id] = project
        return project

    def update_project(self, project_id: str, result: ProjectResult) -> None:
        self._projects[project_id] = result
        payload = {
            "status": result.status.value,
            "result_json": result.outputs,
            "events": [
                {
                    "node": event.node,
                    "message": event.message,
                    "status": event.status.value,
                }
                for event in result.events
            ],
        }
        update_project(project_id, payload, self.client)

    def get_project(self, project_id: str) -> ProjectResult | None:
        if project_id in self._projects:
            return self._projects[project_id]
        row = fetch_project(project_id, self.client)
        if not row:
            return None
        events = [WorkflowEvent(node=e.get("node", ""), message=e.get("message", ""), status=ProjectStatus(e.get("status", ProjectStatus.processing))) for e in row.get("events", [])]
        result = ProjectResult(
            id=row.get("id", project_id),
            theme=row.get("theme", ""),
            status=ProjectStatus(row.get("status", ProjectStatus.processing)),
            outputs=row.get("result_json", {}) or {},
            events=events,
        )
        self._projects[project_id] = result
        return result

    def _hydrate(self) -> None:
        """Load persisted rows into memory when Supabase is configured."""
        if self.client is None:
            return
        try:
            docs = self.client.table("Identity_Docs").select("*").execute().data
            for row in docs:
                doc = IdentityDoc(
                    id=row.get("id"),
                    type=IdentityDocType(row.get("type", IdentityDocType.skill)),
                    content=row.get("content", ""),
                    embedding=row.get("embedding", []) or [],
                    user_id=row.get("user_id"),
                )
                self._docs[doc.id] = doc
        except Exception as exc:  # pragma: no cover - external IO
            logger.warning("Supabase hydrate identity failed: %s", exc)

        try:
            styles = self.client.table("Platform_Styles").select("*").execute().data
            for row in styles:
                platform = PlatformName(row.get("platform", PlatformName.qiita))
                style = PlatformStyle(
                    id=row.get("id"),
                    platform=platform,
                    rules=row.get("rules", {}) or {},
                    version=row.get("version", 1),
                    user_id=row.get("user_id"),
                )
                self._styles[platform] = style
        except Exception as exc:  # pragma: no cover - external IO
            logger.warning("Supabase hydrate style failed: %s", exc)


data_store = DataStore()
