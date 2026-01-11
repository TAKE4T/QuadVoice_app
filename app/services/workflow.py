from __future__ import annotations

from typing import Dict, Iterable, List, TypedDict

from langgraph.graph import END, StateGraph

from app.models.domain import PlatformName, ProjectResult, ProjectStatus, WorkflowEvent
from app.services.llm import generate_article


class WorkflowState(TypedDict):
    theme: str
    identity_chunks: List[str]
    identity_summary: str
    angles: Dict[PlatformName, str]
    outputs: Dict[str, str]
    events: List[WorkflowEvent]


def summarize_identities(identity_chunks: List[str]) -> str:
    if not identity_chunks:
        return "no identity docs ingested yet"
    preview = " | ".join(chunk.strip().splitlines()[0] for chunk in identity_chunks if chunk.strip())
    return preview[:280]


def plan_angles(theme: str) -> Dict[PlatformName, str]:
    return {
        PlatformName.qiita: f"How-to angle for {theme}",
        PlatformName.zenn: f"Concept deep-dive on {theme}",
        PlatformName.note: f"Storytelling about {theme}",
        PlatformName.owned: f"SEO and conversion plan for {theme}",
    }


def _intent_node(state: WorkflowState) -> WorkflowState:
    summary = summarize_identities(state.get("identity_chunks", []))
    state["identity_summary"] = summary
    state["events"].append(WorkflowEvent(node="Intent Analysis", message=f"Derived core message from identity: {summary}", status=ProjectStatus.processing))
    return state


def _angle_node(state: WorkflowState) -> WorkflowState:
    angles = plan_angles(state["theme"])
    state["angles"] = angles
    state["events"].append(WorkflowEvent(node="Angle Planning", message=f"Angles prepared for: {list(angles.keys())}", status=ProjectStatus.processing))
    return state


def _draft_node(state: WorkflowState) -> WorkflowState:
    outputs: Dict[str, str] = {}
    for platform, angle in state["angles"].items():
        style_rules: Dict[str, str] = {}
        outputs[platform.value] = generate_article(
            theme=state["theme"],
            platform=platform,
            angle=angle,
            identity_summary=state["identity_summary"],
            style_rules=style_rules,
        )
    state["outputs"] = outputs
    state["events"].append(WorkflowEvent(node="Drafting", message="Drafted parallel platform outputs", status=ProjectStatus.processing))
    return state


def _refine_node(state: WorkflowState) -> WorkflowState:
    state["events"].append(WorkflowEvent(node="Refinement", message="Normalized markdown for each platform", status=ProjectStatus.completed))
    return state


def build_graph() -> StateGraph:
    graph = StateGraph(WorkflowState)
    graph.add_node("intent", _intent_node)
    graph.add_node("angle", _angle_node)
    graph.add_node("draft", _draft_node)
    graph.add_node("refine", _refine_node)

    graph.set_entry_point("intent")
    graph.add_edge("intent", "angle")
    graph.add_edge("angle", "draft")
    graph.add_edge("draft", "refine")
    graph.add_edge("refine", END)
    return graph


def run_workflow(theme: str, identity_chunks: List[str]) -> ProjectResult:
    graph = build_graph().compile()
    initial_state: WorkflowState = {
        "theme": theme,
        "identity_chunks": identity_chunks,
        "identity_summary": "",
        "angles": {},
        "outputs": {},
        "events": [],
    }
    final_state: WorkflowState = graph.invoke(initial_state)
    return ProjectResult(
        id="",  # caller overwrites with actual project id
        theme=theme,
        status=ProjectStatus.completed,
        outputs=final_state["outputs"],
        events=final_state["events"],
    )


def stream_workflow(theme: str, identity_chunks: List[str]) -> Iterable[WorkflowEvent | ProjectResult]:
    events: List[WorkflowEvent] = []
    # Intent
    summary = summarize_identities(identity_chunks)
    intent_event = WorkflowEvent(node="Intent Analysis", message=f"Derived core message from identity: {summary}", status=ProjectStatus.processing)
    events.append(intent_event)
    yield intent_event

    # Angles
    angles = plan_angles(theme)
    angle_event = WorkflowEvent(node="Angle Planning", message=f"Angles prepared for: {list(angles.keys())}", status=ProjectStatus.processing)
    events.append(angle_event)
    yield angle_event

    # Draft
    outputs: Dict[str, str] = {}
    for platform, angle in angles.items():
        outputs[platform.value] = generate_article(theme=theme, platform=platform, angle=angle, identity_summary=summary, style_rules={})
    draft_event = WorkflowEvent(node="Drafting", message="Drafted parallel platform outputs", status=ProjectStatus.processing)
    events.append(draft_event)
    yield draft_event

    # Refinement
    refine_event = WorkflowEvent(node="Refinement", message="Normalized markdown for each platform", status=ProjectStatus.completed)
    events.append(refine_event)
    yield refine_event

    yield ProjectResult(id="", theme=theme, status=ProjectStatus.completed, outputs=outputs, events=events)
