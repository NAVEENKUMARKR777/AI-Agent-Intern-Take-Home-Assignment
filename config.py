import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    DATABASE_URL = "sqlite:///./plans.db"
    GROQ_MODEL = "llama-3.1-8b-instant"
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
