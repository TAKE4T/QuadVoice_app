from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket

from app.models.domain import ProjectResult, ProjectStatus
from app.models.schemas import GenerateRequest, GenerateResponse, ProjectResultResponse, WorkflowEventResponse
from app.services.stores import data_store
from app.services.workflow import run_workflow, stream_workflow

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(payload: GenerateRequest) -> GenerateResponse:
    project = data_store.create_project(theme=payload.theme)
    identity_chunks = data_store.list_identity_contents()
    result = run_workflow(theme=payload.theme, identity_chunks=identity_chunks)
    result.id = project.id
    data_store.update_project(project_id=project.id, result=result)
    return GenerateResponse(project_id=project.id, status=result.status, preview=result.outputs)


@router.get("/generate/{project_id}", response_model=ProjectResultResponse)
async def get_generation_result(project_id: str) -> ProjectResultResponse:
    project = data_store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectResultResponse(
        project_id=project.id,
        theme=project.theme,
        status=project.status,
        outputs=project.outputs,
        events=[WorkflowEventResponse.from_domain(e) for e in project.events],
    )


@router.websocket("/ws/generate/{project_id}")
async def stream_workflow_route(websocket: WebSocket, project_id: str) -> None:
    await websocket.accept()
    project = data_store.get_project(project_id)
    if not project:
        await websocket.send_json({"error": "project not found"})
        await websocket.close(code=1008)
        return

    identity_chunks = data_store.list_identity_contents()

    try:
        async def run_and_stream() -> None:
            async for item in _async_stream(identity_chunks, project.theme, project.id):
                if isinstance(item, WorkflowEventResponse):
                    await websocket.send_json(item.dict())
                elif isinstance(item, ProjectResult):
                    await websocket.send_json({"status": item.status, "outputs": item.outputs})
            await websocket.close()

        await run_and_stream()
    except Exception as exc:  # pragma: no cover - network path
        await websocket.send_json({"error": str(exc)})
        await websocket.close(code=1011)


async def _async_stream(identity_chunks: list[str], theme: str, project_id: str):
    for item in stream_workflow(theme=theme, identity_chunks=identity_chunks):
        if isinstance(item, ProjectResult):
            item.id = project_id
            data_store.update_project(project_id=project_id, result=item)
            yield item
        else:
            yield WorkflowEventResponse.from_domain(item)
