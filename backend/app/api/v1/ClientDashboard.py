import json
from typing import Optional
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    dependencies,
    Depends,
    status,
)
from ...models.job import Job
from ...models.user import User
from sqlalchemy.orm import Session
from .auth import get_db, get_current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from ...middleware.redis import make_cache_key, redis

router = APIRouter()


@router.get("/job/Panel")
def client_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of jobs per page"),
    status: Optional[str] = Query(
        None, description="Filter by job status (e.g., open, closed)"
    ),
    work_mode: Optional[str] = Query(
        None, description="Filter by work mode (e.g., remote, on-site, hybrid)"
    ),
    category: Optional[str] = Query(None, description="Filter by job category"),
    search: Optional[str] = Query(None, description="Search in title or description"),
    sort_by: str = Query(
        "created_at", description="Sort by field (created_at, budget, deadline)"
    ),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    query = db.query(Job).filter(Job.user_id == user.id)

    if status:
        query = query.filter(Job.status == status)
    if work_mode:
        query = query.filter(Job.work_mode == work_mode)
    if category:
        query = query.filter(Job.category == category)
    if search:
        query = query.filter(
            (Job.title.ilike(f"%{search}%"))
            | (Job.job_description.ilike(f"%{search}%"))
        )

    sort_field = {
        "created_at": Job.created_at,
        "budget": Job.budget,
        "deadline": Job.deadline,
    }.get(sort_by, Job.created_at)
    query = query.order_by(
        sort_field.desc() if sort_order.lower() == "desc" else sort_field.asc()
    )

    total_jobs = query.count()
    jobs = query.offset((page - 1) * page_size).limit(page_size).all()

    if not jobs and page == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user does not have any jobs matching the criteria",
        )

    try:
        # Calculate total budget
        total_budget = (
            db.query(func.sum(Job.budget)).filter(Job.user_id == user.id).scalar()
            or 0.0
        )

        # Calculate job statistics
        stats_query = (
            db.query(Job.status, Job.work_mode, func.count(Job.id))
            .filter(Job.user_id == user.id)
            .group_by(Job.status, Job.work_mode)
            .all()
        )
        job_stats = [
            {"status": s, "work_mode": wm, "count": c} for s, wm, c in stats_query
        ]

        # Prepare response
        response_data = {
            "total_budget": total_budget,
            "total_jobs": total_jobs,
            "page": page,
            "page_size": page_size,
            "job_stats": job_stats,
            "jobs": [
                {
                    "project_title": job.title,
                    "start_day": job.created_at.isoformat(),
                    "current_status": job.status,  # Use actual status field
                    "last_update": job.updated_at.isoformat(),
                    "job_description": job.job_description,
                    "budget": job.budget,
                    "deadline": job.deadline.isoformat() if job.deadline else None,
                    "work_mode": job.work_mode,
                    "category": job.category,
                    "location": job.location,
                    "job_type": job.job_type,
                    "visibility": job.visibility,
                    "payment_status": job.payment_status,
                }
                for job in jobs
            ],
        }

        return response_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {e}",
        )


@router.get("/Admin/Dashboard")
def admin_dashboard(
    requset: Request,
    db: Session = Depends(get_db),
    limit: int = Query(ge=5, le=20, default=5),
    offset: int = Query(ge=0, le=10, default=0),
    category: Optional[str] = Query(default=None),
    start_date: datetime = Query(default=None),
):
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    cache_reponse = make_cache_key(str(requset.url.path), dict(requset.query_params))
    cached = redis.get(cache_reponse)
    if cached:
        return {"from redis": json.loads(cached)}

    #  Total users grouped by role
    total_users_by_role = (
        db.query(User.role, func.count(User.id).label("count"))
        .group_by(User.role)
        .all()
    )

    #  New users in the last 7 days
    new_users = (
        db.query(User)
        .filter(User.created_at >= week_ago)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    #  New jobs posted in the last 7 days
    new_jobs = (
        db.query(Job)
        .filter(Job.created_at >= week_ago)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    #  Job category counts (optional filter)
    job_category_query = (
        db.query(Job.category, func.count(Job.id).label("count"))
        .group_by(Job.category)
        .order_by(func.count(Job.id).desc())
    )

    if category:
        job_category_query = job_category_query.filter(Job.category == category)

    job_categories = job_category_query.limit(limit).offset(offset).all()

    # Structured response

    response = {
        "total_users_by_role": [
            {"role": role, "count": count} for role, count in total_users_by_role
        ],
        "new_users": [{"name": user.name, "email": user.email} for user in new_users],
        "new_jobs": [
            {"title": job.title, "description": job.job_description} for job in new_jobs
        ],
        "job_category_counts": [
            {"category": category, "count": count} for category, count in job_categories
        ],
    }
    redis.setex(cache_reponse, 60, json.dumps(response))
    return response
