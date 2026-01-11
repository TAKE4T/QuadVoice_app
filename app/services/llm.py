from __future__ import annotations

import hashlib
import logging
from typing import Dict, List, Optional

from anthropic import Anthropic

from app.core.config import settings
from app.models.domain import PlatformName

logger = logging.getLogger(__name__)


def embed_text(text: str, dimensions: int) -> List[float]:
    # Simple deterministic hash-based embedding for local dev; replace with real embedding model in production.
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    floats = [byte / 255.0 for byte in digest]
    # Repeat/truncate to match dimensions
    result: List[float] = (floats * (dimensions // len(floats) + 1))[:dimensions]
    return result


def _get_anthropic_client() -> Optional[Anthropic]:
    if not settings.anthropic_api_key:
        return None
    try:
        return Anthropic(api_key=settings.anthropic_api_key)
    except Exception as exc:  # pragma: no cover - external init
        logger.warning("Failed to init Anthropic client: %s", exc)
        return None


def generate_article(theme: str, platform: PlatformName, angle: str, identity_summary: str, style_rules: Dict[str, str]) -> str:
    client = _get_anthropic_client()
    prompt = (
        f"You are drafting an article for {platform.value}.\n"
        f"Theme: {theme}\n"
        f"Angle: {angle}\n"
        f"Identity summary: {identity_summary}\n"
        f"Style hints: {style_rules}\n"
        "Return concise markdown with intro, 3 bullets, and takeaway."
    )
    if not client:
        return (
            f"# {theme} — {platform.value}\n"
            f"- Angle: {angle}\n"
            f"- Voice: {identity_summary}\n"
            "## Intro\nPlaceholder intro.\n\n"
            "## Points\n- Point A\n- Point B\n- Point C\n\n"
            "## Takeaway\nKey takeaway here.\n"
        )

    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=800,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text  # type: ignore[no-any-return]
    except Exception as exc:  # pragma: no cover - external call
        logger.warning("Anthropic generation failed, falling back to stub: %s", exc)
        return (
            f"# {theme} — {platform.value}\n"
            f"- Angle: {angle}\n"
            f"- Voice: {identity_summary}\n"
            "## Intro\nLLM unavailable; stub content.\n\n"
            "## Points\n- Point A\n- Point B\n- Point C\n\n"
            "## Takeaway\nKey takeaway here.\n"
        )
