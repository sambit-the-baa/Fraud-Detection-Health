from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from dotenv import load_dotenv

# Rate limiting (optional - comment out if slowapi not installed)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    print("Warning: slowapi not installed. Rate limiting disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from database import SessionLocal, engine, Base
from models import Policy, Claim, Document, Question
from schemas import (
    PolicyVerificationRequest, PolicyVerificationResponse,
    ClaimCreate, ClaimResponse, ClaimDetailResponse, ClaimsListResponse,
    DocumentUploadResponse, QuestionRequest, QuestionResponse,
    FraudAnalysisResponse, ClaimStatusUpdate
)
from services.policy_service import PolicyService
from services.document_service import DocumentService
from services.ai_service import AIService

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Health Insurance Claim Portal", version="1.0.0")

# Rate limiting (optional)
if RATE_LIMITING_ENABLED:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    # Create a dummy limiter decorator that does nothing
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = DummyLimiter()

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://fraud-detection-health-frontend.onrender.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve static files from frontend build
FRONTEND_BUILD_PATH = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_BUILD_PATH.exists():
    # Mount static files (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_BUILD_PATH / "assets")), name="assets")
    
    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # If path starts with /api, let FastAPI handle it
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        
        # Serve index.html for all other routes
        index_file = FRONTEND_BUILD_PATH / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not found"}

# Global exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "message": "Invalid input data provided"
        }
    )

# Global exception handler for HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize services
policy_service = PolicyService()
document_service = DocumentService()
ai_service = AIService()

@app.get("/")
async def root():
    return {"message": "Health Insurance Claim Portal API"}

@app.post("/api/verify-policy", response_model=PolicyVerificationResponse)
async def verify_policy(
    request: Request,
    policy_data: PolicyVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify if policy exists and is valid"""
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

@app.post("/api/claims", response_model=ClaimResponse)
async def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db)
):
    """Create a new claim"""
    policy = db.query(Policy).filter(Policy.policy_number == claim_data.policy_number).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    claim = Claim(
        policy_number=claim_data.policy_number,
        claim_type=claim_data.claim_type,
        incident_date=claim_data.incident_date,
        description=claim_data.description,
        status="pending"
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    
    return ClaimResponse(
        id=claim.id,
        policy_number=claim.policy_number,
        claim_type=claim.claim_type,
        incident_date=claim.incident_date.isoformat(),
        status=claim.status,
        created_at=claim.created_at.isoformat(),
        fraud_score=claim.fraud_score,
        fraud_risk_level=claim.fraud_risk_level
    )

@app.post("/api/claims/{claim_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    claim_id: int,
    file: UploadFile = File(...),
    document_type: str = None,
    db: Session = Depends(get_db)
):
    """Upload a document for a claim"""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    document = await document_service.upload_document(
        db, claim_id, file, document_type or file.filename
    )
    
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        document_type=document.document_type,
        uploaded_at=document.uploaded_at.isoformat()
    )

@app.post("/api/claims/{claim_id}/ask-question", response_model=QuestionResponse)
async def ask_question(
    claim_id: int,
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """AI-powered questioning about the claim"""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get claim context
    documents = db.query(Document).filter(Document.claim_id == claim_id).all()
    previous_questions = db.query(Question).filter(Question.claim_id == claim_id).all()
    
    response = await ai_service.ask_question(
        db, claim, request.user_message, documents, previous_questions
    )
    
    return response

@app.post("/api/claims/{claim_id}/analyze-fraud", response_model=FraudAnalysisResponse)
async def analyze_fraud(
    claim_id: int,
    db: Session = Depends(get_db)
):
    """Perform comprehensive fraud analysis"""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    documents = db.query(Document).filter(Document.claim_id == claim_id).all()
    questions = db.query(Question).filter(Question.claim_id == claim_id).all()
    
    analysis = await ai_service.analyze_fraud_risk(db, claim, documents, questions)
    
    return analysis

@app.get("/api/claims/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim(
    claim_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed claim information"""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    documents = db.query(Document).filter(Document.claim_id == claim_id).all()
    questions_count = db.query(Question).filter(Question.claim_id == claim_id).count()
    
    return ClaimDetailResponse(
        id=claim.id,
        policy_number=claim.policy_number,
        claim_type=claim.claim_type,
        incident_date=claim.incident_date.isoformat(),
        description=claim.description,
        status=claim.status,
        fraud_score=claim.fraud_score,
        fraud_risk_level=claim.fraud_risk_level,
        created_at=claim.created_at.isoformat(),
        updated_at=claim.updated_at.isoformat() if claim.updated_at else claim.created_at.isoformat(),
        documents=[{
            "id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "uploaded_at": doc.uploaded_at.isoformat()
        } for doc in documents],
        questions_count=questions_count
    )

@app.get("/api/policies/{policy_number}/claims", response_model=ClaimsListResponse)
async def get_policy_claims(
    policy_number: str,
    db: Session = Depends(get_db)
):
    """Get all claims for a policy"""
    claims = db.query(Claim).filter(Claim.policy_number == policy_number).order_by(Claim.created_at.desc()).all()
    
    return ClaimsListResponse(
        claims=[ClaimResponse(
            id=claim.id,
            policy_number=claim.policy_number,
            claim_type=claim.claim_type,
            incident_date=claim.incident_date.isoformat(),
            status=claim.status,
            created_at=claim.created_at.isoformat(),
            fraud_score=claim.fraud_score,
            fraud_risk_level=claim.fraud_risk_level
        ) for claim in claims],
        total=len(claims)
    )

@app.patch("/api/claims/{claim_id}/status", response_model=ClaimResponse)
async def update_claim_status(
    claim_id: int,
    status_update: ClaimStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update claim status (admin function)"""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    valid_statuses = ["pending", "under_review", "approved", "rejected"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    claim.status = status_update.status
    db.commit()
    db.refresh(claim)
    
    return ClaimResponse(
        id=claim.id,
        policy_number=claim.policy_number,
        claim_type=claim.claim_type,
        incident_date=claim.incident_date.isoformat(),
        status=claim.status,
        created_at=claim.created_at.isoformat(),
        fraud_score=claim.fraud_score,
        fraud_risk_level=claim.fraud_risk_level
    )

@app.get("/api/claims", response_model=ClaimsListResponse)
async def get_all_claims(
    policy_number: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all claims with optional filters (admin function)"""
    query = db.query(Claim)
    
    if policy_number:
        query = query.filter(Claim.policy_number == policy_number)
    if status:
        query = query.filter(Claim.status == status)
    
    claims = query.order_by(Claim.created_at.desc()).all()
    
    return ClaimsListResponse(
        claims=[ClaimResponse(
            id=claim.id,
            policy_number=claim.policy_number,
            claim_type=claim.claim_type,
            incident_date=claim.incident_date.isoformat(),
            status=claim.status,
            created_at=claim.created_at.isoformat(),
            fraud_score=claim.fraud_score,
            fraud_risk_level=claim.fraud_risk_level
        ) for claim in claims],
        total=len(claims)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

