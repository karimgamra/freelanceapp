from fastapi import FastAPI
from .api.v1 import users, profiles, jobs
from .db.database import Base, engine
from app.middleware.redis import RateLimitMiddleware
from app.api.v1 import ClientDashboard

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(RateLimitMiddleware)


app.include_router(users.router, prefix="/app/api/v1/users", tags=["users"])
app.include_router(profiles.router, prefix="/app/api/v1/profiles", tags=["profiles"])
app.include_router(jobs.router, prefix="/app/api/v1/jobs", tags=["jobs"])
app.include_router(
    ClientDashboard.router,
    prefix="/app/api/v1/ClientDashboard",
    tags=["ClientDashboard"],
)
