from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


DATA_BASE_URL = "postgresql://karim:123@localhost:5432/freelancer_db"

engine = create_engine(DATA_BASE_URL)
sessionLocal = sessionmaker(bind=engine ,autoflush=False ,autocommit=False)

Base = declarative_base()


