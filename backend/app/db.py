import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Loads environment variables from .env early
load_dotenv()

# Read DATABASE_URL securely from env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Check your .env file.")

# Step 4: Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

#Creates a session factory for request-level sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base class for ORM models (used for prediction logging tables)
Base = declarative_base()


#FastAPI dependency generator for request database sessions
def get_db():
    """
    Yields a database session for an API request, ensuring 
    the session is safely closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()