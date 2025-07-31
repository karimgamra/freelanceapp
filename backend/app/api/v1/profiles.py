from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ...db.dependencies.get_db import get_db
from ...schemas.profile import CreateProfile, UpdateProfile
from .auth import get_current_user
from ...models.user import User
from ...models.profile import Profile
from ...utils.crud import (
    create_instance,
    get_instance_or_404,
    update_instance,
    delete_instance,
)
from typing import Optional

router = APIRouter()


def get_user_profile(user: User, db: Session) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for the user",
        )
    return profile


@router.post("/profile")
def create_profile(
    profile: CreateProfile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing_profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a profile",
        )

    try:
        skills_str = ",".join(profile.skills)
        profile_data = profile.dict(exclude={"skills"})
        new_profile = create_instance(
            db, Profile, user_id=user.id, skills=skills_str, **profile_data
        )
        return {
            "message": "Profile created successfully",
            "profile_id": new_profile.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/profile")
def get_my_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = get_instance_or_404(db, Profile)
    return {
        "bio": profile.bio,
        "skills": profile.skills.split(",") if profile.skills else [],
        "experience": profile.experience,
        "location": profile.location,
        "hourly_rate": profile.hourly_rate,
        "available": profile.available,
    }


@router.put("/profile")
def update_profile(
    update_profile: UpdateProfile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = get_user_profile(user, db)
    update_data = update_profile.dict(exclude_unset=True)

    if "skills" in update_data:
        update_data["skills"] = ",".join(update_data["skills"])

    updated_profile = update_instance(db, profile, update_data)

    return {"message": "Profile updated successfully", "profile_id": updated_profile.id}


@router.delete("/profile")
def delete_user_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = get_user_profile(user, db)
    delete_instance(db, profile)
    return {"message": "Profile deleted successfully"}


@router.get("/freelancers/search")
def search_freelancers(
    skill: Optional[str] = Query(None, description="Comma separated list of skills"),
    min_rate: Optional[float] = Query(None),
    max_rate: Optional[float] = Query(None),
    location: Optional[str] = Query(None),
    available: Optional[bool] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query(
        None, description="Sort by 'hourly_rate', 'available', or 'location'"
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    if user.role not in ("client", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    query = db.query(Profile).join(User)

    if skill:
        skills_list = [s.strip().lower() for s in skill.split(",")]

        from sqlalchemy import or_

        skill_filters = [Profile.skills.ilike(f"%{s}%") for s in skills_list]
        query = query.filter(or_(*skill_filters))

    if min_rate is not None:
        query = query.filter(Profile.hourly_rate >= min_rate)

    if max_rate is not None:
        query = query.filter(Profile.hourly_rate <= max_rate)

    if location:
        query = query.filter(Profile.location.ilike(f"%{location}%"))

    if available is not None:
        query = query.filter(Profile.available == available)

    if sort_by:
        if sort_by == "hourly_rate":
            query = query.order_by(Profile.hourly_rate.asc())
        elif sort_by == "available":
            query = query.order_by(Profile.available.desc())
        elif sort_by == "location":
            query = query.order_by(Profile.location.asc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort_by value")

    total = query.count()
    results = query.limit(limit).offset(offset).all()

    response = [
        {
            "name": profile.user.name,
            "email": profile.user.email,
            "bio": profile.bio,
            "skills": profile.skills.split(",") if profile.skills else [],
            "portfolio_links": profile.portfolio_links,
            "location": profile.location,
            "hourly_rate": profile.hourly_rate,
            "available": profile.available,
        }
        for profile in results
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "freelancers": response,
    }
