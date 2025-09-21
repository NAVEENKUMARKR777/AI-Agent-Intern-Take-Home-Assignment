from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    goal = Column(Text, nullable=False)
    plan_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create database tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
