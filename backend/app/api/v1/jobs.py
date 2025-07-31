from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.models.job import Job
from ...models.user import User
from app.schemas.job import CreateJob, UpdateJob
from .auth import get_current_user, get_db
from ...utils.crud import create_instance, get_instance_or_404, update_instance
from ...utils.exceptions import raise_not_found, raise_sever_error
from ...utils.users import ensure_client
from sqlalchemy import asc, desc
from ...middleware.redis import make_cache_key, redis
from ...schemas.job import JobResponse
import json, hashlib

router = APIRouter()


@router.post("/job", status_code=status.HTTP_201_CREATED)
def post_job(
    job: CreateJob,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    raise_not_found(user, "")
    ensure_client(user)

    try:
        new_job = create_instance(db, Job, user_id=user.id, **job.dict())

        return {
            "message": "Job posted successfully",
            "job": {
                "id": new_job.id,
                "title": new_job.title,
                "location": new_job.location,
                "budget": new_job.budget,
                "is_active": new_job.is_active,
            },
        }

    except Exception as e:
        db.rollback()
        detail = f"An error occurred while posting the job {e}"
        raise_sever_error(db, detail)


@router.get("/jobs")
def get_job(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = db.query(Job).filter(Job.user_id == user.id).all()
    return jobs


@router.put("/job/{job_id}")
def update_job(
    job_id: UUID,
    job_data: UpdateJob,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == str(job_id)).first()
    if not job:
        raise_not_found(job)
    updated_job = update_instance(db, job, job_data.dict())
    return updated_job


@router.delete("/job/{job_id}")
def delete_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == str(job_id)).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully", "job_id": str(job_id)}


@router.get(
    "/search",
)
def search_jobs(
    request: Request,
    query: Optional[str] = Query(
        None, description="Search by job title or description"
    ),
    skills: Optional[List[str]] = Query(None, description="Filter by skills"),
    location: Optional[str] = Query(None, description="Filter by location"),
    budget_min: Optional[float] = Query(None, ge=0, description="Minimum budget"),
    budget_max: Optional[float] = Query(None, ge=0, description="Maximum budget"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    order_by: Optional[str] = Query("created_at", description="Order by field"),
    direction: Optional[str] = Query(
        "desc", enum=["asc", "desc"], description="Sort direction"
    ),
    limit: int = Query(10, ge=1, le=10, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """Search for jobs with flexible filtering and pagination."""
    cache_key = make_cache_key(str(request.url.password), dict(request.query_params))
    cached = redis.get(cache_key)
    if cached:
        return {"from redis": json.loads(cached)}
    query_set = db.query(Job).filter(Job.is_active == True)

    if query:
        query = f"%{query.lower()}%"
        query_set = query_set.filter(
            (Job.title.ilike(query)) | (Job.job_description.ilike(query))
        )

    if skills:
        for skill in skills:
            skill = f"%{skill.lower()}%"
            query_set = query_set.filter(Job.job_description.ilike(skill))

    if location:
        query_set = query_set.filter(Job.location.ilike(f"%{location.lower()}%"))

    if budget_min is not None:
        query_set = query_set.filter(Job.budget >= budget_min)

    if budget_max is not None:
        query_set = query_set.filter(Job.budget <= budget_max)

    if job_type:
        query_set = query_set.filter(Job.job_type == job_type)

    allowed_order_fields = {
        "title": Job.title,
        "budget": Job.budget,
        "created_at": Job.created_at,
        "location": Job.location,
    }
    order_field = allowed_order_fields.get(order_by, Job.created_at)

    query_set = query_set.order_by(
        asc(order_field) if direction == "asc" else desc(order_field)
    )

    total = query_set.count()

    results = query_set.offset(offset).limit(limit).all()

    response_data = {
        "jobs": [JobResponse.from_orm(job).dict() for job in results],
        "total": total,
        "offset": offset,
        "limit": limit,
    }

    redis.setex(cache_key, 60, json.dumps(response_data))

    return {"jobs": results, "total": total, "offset": offset, "limit": limit}
