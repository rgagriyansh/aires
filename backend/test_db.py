from database import engine
from models import Base

def test_connection():
    try:
        # Try to create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database connection successful!")
        print("✅ Tables created successfully!")
        
        # Try to execute a simple query
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("✅ Simple query executed successfully!")
            
    except Exception as e:
        print("❌ Database connection failed!")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 