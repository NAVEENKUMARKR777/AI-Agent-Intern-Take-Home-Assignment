from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uvicorn

from database import get_db, create_tables, Plan
from agent import TaskPlanningAgent
from config import Config

# Create tables
create_tables()

app = FastAPI(title="AI Task Planning Agent (Groq + Llama 3.1 8B Instant)", version="1.0.0")

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize agent
agent = TaskPlanningAgent(debug_mode=Config.DEBUG_MODE)

# Pydantic models
class GoalRequest(BaseModel):
    goal: str

class PlanResponse(BaseModel):
    id: int
    goal: str
    plan_content: str
    created_at: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main page with goal input form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/plan", response_model=PlanResponse)
async def create_plan(goal_request: GoalRequest, db: Session = Depends(get_db)):
    """Create a new plan from a goal"""
    try:
        # Create plan using agent
        result = agent.create_plan(goal_request.goal)
        
        # Save to database
        db_plan = Plan(
            goal=result["goal"],
            plan_content=result["plan"]
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        
        return PlanResponse(
            id=db_plan.id,
            goal=db_plan.goal,
            plan_content=db_plan.plan_content,
            created_at=db_plan.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plans", response_model=List[PlanResponse])
async def get_plans(db: Session = Depends(get_db)):
    """Get all plans"""
    plans = db.query(Plan).order_by(Plan.created_at.desc()).all()
    return [
        PlanResponse(
            id=plan.id,
            goal=plan.goal,
            plan_content=plan.plan_content,
            created_at=plan.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        for plan in plans
    ]

@app.get("/api/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific plan by ID"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return PlanResponse(
        id=plan.id,
        goal=plan.goal,
        plan_content=plan.plan_content,
        created_at=plan.created_at.strftime("%Y-%m-%d %H:%M:%S")
    )

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """History page showing all plans"""
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": Config.GROQ_MODEL,
        "database": "connected",
        "debug_mode": Config.DEBUG_MODE,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/debug")
async def toggle_debug_mode():
    """Toggle debug mode (development only)"""
    if not Config.DEBUG_MODE:
        return {"message": "Debug mode is disabled. Set DEBUG_MODE=true in .env to enable."}
    
    # Reinitialize agent with toggled debug mode
    global agent
    agent = TaskPlanningAgent(debug_mode=not agent.debug_mode)
    
    return {
        "debug_mode": agent.debug_mode,
        "message": f"Debug mode {'enabled' if agent.debug_mode else 'disabled'}"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
