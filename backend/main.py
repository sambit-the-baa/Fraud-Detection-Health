from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import os
import logging
from dotenv import load_dotenv

# Import your app logic (schemas, services, models, etc.)
from database import SessionLocal, engine, Base
from models import Policy, Claim, Document, Question
from schemas import (PolicyVerificationRequest, PolicyVerificationResponse, ClaimCreate, ClaimResponse, ClaimDetailResponse, ClaimsListResponse, DocumentUploadResponse, QuestionRequest, QuestionResponse, FraudAnalysisResponse, ClaimStatusUpdate)
from services.policy_service import PolicyService
from services.document_service import DocumentService
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# DB table init
Base.metadata.create_all(bind=engine)

# --- Initialize FastAPI ---
app = FastAPI(title="Health Insurance Claim Portal", version="1.0.0")

# --- CORS Middleware ---
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://fraud-detection-health-frontend.onrender.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Error", "detail": exc.errors(), "message": "Invalid input data provided"}
    )
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code, "message": exc.detail}
    )

# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Services ---
policy_service = PolicyService()
document_service = DocumentService()
ai_service = AIService()

# --- API Endpoints ---
@app.get("/api")
def api_root():
    return {"message": "API root: Health Insurance Claim Portal"}

@app.post("/api/seed-database")
async def seed_database(db: Session = Depends(get_db)):
    from seed_data import seed_policies
    try:
        seed_policies()
        return {"message": "Database seeded successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Error seeding db: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to seed db: {e}")

@app.post("/api/verify-policy", response_model=PolicyVerificationResponse)
async def verify_policy(request: Request, policy_data: PolicyVerificationRequest, db: Session = Depends(get_db)):
    policy = policy_service.verify_policy(db, policy_data.policy_number)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyVerificationResponse(
        valid=True,
        policy_number=policy.policy_number,
        policy_holder_name=policy.policy_holder_name,
        policy_type=policy.policy_type,
        expiry_date=policy.expiry_date.isoformat() if policy.expiry_date else None
    )
# ... (continue your other /api/... endpoints here as already written)

# --- Serve React Frontend Build ---
FRONTEND_BUILD_PATH = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_BUILD_PATH.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD_PATH / "assets"), name="assets")

    # Serve SPA's index.html for non-API routes
    @app.get("/{full_path:path}")
    async def spa_handler(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        index_file = FRONTEND_BUILD_PATH / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"error": "Frontend not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
