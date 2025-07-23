from fastapi import FastAPI
from .api.v1 import users
from .db.database import Base ,engine
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router , prefix="/app/api/v1/users.py", tags=["users"])