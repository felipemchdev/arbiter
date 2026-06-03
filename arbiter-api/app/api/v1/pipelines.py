from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.schemas.pipeline import DagDefinitionRead, PipelineCreate, PipelineDetail, PipelineRead, PipelineRunSummary
from app.services.pipeline_service import create_pipeline, get_pipeline, get_pipeline_runs, list_pipelines

router = APIRouter()


@router.get("", response_model=list[PipelineRead])
async def read_pipelines(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return await list_pipelines(db, current_org.id, limit=limit, offset=offset)


@router.post("", response_model=PipelineRead, status_code=status.HTTP_201_CREATED)
async def create_pipeline_endpoint(
    payload: PipelineCreate,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    return await create_pipeline(db, current_org.id, payload)


@router.get("/{pipeline_id}", response_model=PipelineDetail)
async def read_pipeline(
    pipeline_id: str,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await get_pipeline(db, pipeline_id, current_org.id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pipeline not found")
    dag_definition = pipeline.dag_definition
    payload = {
        "id": pipeline.id,
        "name": pipeline.name,
        "source": pipeline.source,
        "dag_id": pipeline.dag_id,
        "last_run_status": pipeline.last_run_status,
        "last_run_at": pipeline.last_run_at,
        "created_at": pipeline.created_at,
        "dag_definition": None
        if dag_definition is None
        else DagDefinitionRead(nodes=dag_definition.nodes, edges=dag_definition.edges, updated_at=dag_definition.updated_at),
    }
    return PipelineDetail.model_validate(payload)


@router.get("/{pipeline_id}/runs", response_model=list[PipelineRunSummary])
async def read_pipeline_runs(
    pipeline_id: str,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    pipeline = await get_pipeline(db, pipeline_id, current_org.id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pipeline not found")
    return await get_pipeline_runs(db, pipeline.id, limit, offset)