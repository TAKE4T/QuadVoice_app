from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.core.config import settings


logger = logging.getLogger(__name__)


def get_supabase_client() -> Optional[Client]:
    if not settings.supabase_url or not settings.supabase_service_key:
        logger.warning("Supabase credentials missing; falling back to in-memory store")
        return None
    try:
        return create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as exc:  # pragma: no cover - external client init
        logger.warning("Failed to initialize Supabase client: %s", exc)
        return None


def upsert(table: str, payload: Dict[str, Any], client: Client | None) -> None:
    if client is None:
        return
    try:
        client.table(table).upsert(payload, on_conflict="id").execute()
    except Exception as exc:  # pragma: no cover - external IO
        logger.warning("Supabase upsert failed for %s: %s", table, exc)


def insert(table: str, payload: Dict[str, Any], client: Client | None) -> None:
    if client is None:
        return
    try:
        client.table(table).insert(payload).execute()
    except Exception as exc:  # pragma: no cover - external IO
        logger.warning("Supabase insert failed for %s: %s", table, exc)


def fetch_project(project_id: str, client: Client | None) -> Optional[Dict[str, Any]]:
    if client is None:
        return None
    try:
        response = client.table("Projects").select("*").eq("id", project_id).execute()
        data = response.data
        if data:
            return data[0]
    except Exception as exc:  # pragma: no cover - external IO
        logger.warning("Supabase fetch project failed: %s", exc)
    return None


def update_project(project_id: str, payload: Dict[str, Any], client: Client | None) -> None:
    if client is None:
        return
    try:
        client.table("Projects").update(payload).eq("id", project_id).execute()
    except Exception as exc:  # pragma: no cover - external IO
        logger.warning("Supabase update project failed: %s", exc)
