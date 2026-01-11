from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import settings
from app.models.domain import IdentityDocType, PlatformName
from app.models.schemas import IdentityIngestResponse, StyleIngestResponse
from app.services.llm import embed_text
from app.services.stores import data_store

router = APIRouter(tags=["ingest"])


@router.post("/ingest/identity", response_model=IdentityIngestResponse)
async def ingest_identity(doc_type: IdentityDocType = Form(...), files: list[UploadFile] = File(...)) -> IdentityIngestResponse:
    doc_ids: list[str] = []
    for file in files:
        payload = await file.read()
        content = payload.decode("utf-8", errors="ignore")
        embedding = embed_text(content, settings.embedding_dimensions)
        doc = data_store.save_identity(doc_type=doc_type, content=content, embedding=embedding)
        doc_ids.append(doc.id)
    return IdentityIngestResponse(count=len(doc_ids), doc_ids=doc_ids)


@router.post("/ingest/style", response_model=StyleIngestResponse)
async def ingest_style(platform: PlatformName = Form(...), file: UploadFile = File(...)) -> StyleIngestResponse:
    payload = await file.read()
    content = payload.decode("utf-8", errors="ignore")
    first_heading = next((line.strip("# ") for line in content.splitlines() if line.startswith("#")), "Untitled")
    rules = {
        "tone": "auto-detected",
        "outline_hint": first_heading,
        "notes": "Stored locally; replace with LLM extraction and persist to Supabase",
    }
    style = data_store.save_style(platform=platform, rules=rules)
    return StyleIngestResponse(platform=style.platform, version=style.version, summary=style.rules)
