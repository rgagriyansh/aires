from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment variable (for production)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production environment (Render)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    # Local development environment
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mslm12345")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "userdb")
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.debug(f"Database URL: {SQLALCHEMY_DATABASE_URL}")

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Function to verify table schema
def verify_schema():
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.debug(f"Existing tables: {tables}")
        
        for table in tables:
            columns = inspector.get_columns(table)
            logger.debug(f"Columns in {table}:")
            for column in columns:
                logger.debug(f"  - {column['name']}: {column['type']}")
    except Exception as e:
        logger.error(f"Error verifying schema: {str(e)}")
        raise

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()

# Verify schema on import
verify_schema() 
