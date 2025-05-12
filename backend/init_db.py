from sqlalchemy import text
from database import engine, Base
from models import User, ResearchPaper

def init_db():
    try:
        # Drop all existing tables
        Base.metadata.drop_all(bind=engine)
        print("Dropped existing tables")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Created new tables")
        
        # Verify the confirmed_sections column exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'research_papers' 
                AND column_name = 'confirmed_sections'
            """))
            if not result.fetchone():
                print("Warning: confirmed_sections column not found in research_papers table")
            else:
                print("Verified confirmed_sections column exists")
        
        print("Database initialization completed successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 