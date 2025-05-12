import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    # Only show first 10 characters for security
    print(f"API key found! First 10 characters: {api_key[:10]}...")
    print("Environment variables are working correctly!")
else:
    print("Error: API key not found. Make sure .env file exists and contains OPENAI_API_KEY") 