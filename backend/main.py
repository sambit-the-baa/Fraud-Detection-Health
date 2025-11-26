from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from bson import ObjectId
# MongoDB migration - removed SQLAlchemy import
import os
import logging
from dotenv import load_dotenv
from typing import List, Optional

# Import your other modules
from database import get_sync_db
import models
import schemas
from services.policy_service import PolicyService
from services.ai_service import AIService
from services.document_service import DocumentService

# Seed sample policies in MongoDB
def seed_sample_policies():
    """Insert sample policies if collection is empty"""
    try:
        db = get_sync_db()
        if db.policies.count_documents({}) == 0:
            from datetime import datetime, timedelta
            sample_policies = [
                {
                    "policy_number": "POL-2024-001",
                    "policy_holder_name": "John Smith",
                    "policy_type": "Premium Health",
                    "expiry_date": datetime.now() + timedelta(days=365),
                    "created_at": datetime.now(),
                    "status": "active"
                },
                {
                    "policy_number": "POL-2024-002",
                    "policy_holder_name": "Jane Doe",
                    "policy_type": "Basic Health",
                    "expiry_date": datetime.now() + timedelta(days=180),
                    "created_at": datetime.now(),
                    "status": "active"
                },
                {
                    "policy_number": "POL-2024-003",
                    "policy_holder_name": "Bob Johnson",
                    "policy_type": "Family Health",
                    "expiry_date": datetime.now() + timedelta(days=730),
                    "created_at": datetime.now(),
                    "status": "active"
                },
            ]
            db.policies.insert_many(sample_policies)
            db.policies.create_index("policy_number", unique=True)
            print("Sample policies seeded successfully")
    except Exception as e:
        print(f"Error seeding policies: {e}")

# Call seed function on startup
seed_sample_policies()

# Initialize services
policy_service = PolicyService()
ai_service = AIService()
document_service = DocumentService()

def get_db():
        # MongoDB migration - using get_sync_db() from database module
    return get_sync_db()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# Initialize app
app = FastAPI(title="Health Insurance Claim Portal", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fraud-detection-health-frontend.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== POLICY ROUTES ====================

@app.post("/api/verify-policy", response_model=schemas.PolicyVerificationResponse)
async def verify_policy(request: schemas.PolicyVerificationRequest, db = Depends(get_db)):
    """Verify if a policy exists and is valid"""
    policy = policy_service.verify_policy(db, request.policy_number)
    
    if not policy:
        return schemas.PolicyVerificationResponse(
            valid=False,
            policy_number=request.policy_number,
            policy_holder_name="",
            policy_type="",
            expiry_date=None
        )
    
    return schemas.PolicyVerificationResponse(
        valid=True,
        policy_number=policy["policy_number"],
        policy_holder_name=policy["policy_holder_name"],
        policy_type=policy["policy_type"],
        expiry_date=policy["expiry_date"].isoformat() if policy["expiry_date"] else None
    )

# ==================== CLAIMS ROUTES ====================

@app.post("/api/claims", response_model=schemas.ClaimResponse)
async def create_claim(claim: schemas.ClaimCreate, db = Depends(get_db)):
    """Create a new insurance claim"""
    # Verify policy exists
    policy = policy_service.verify_policy(db, claim.policy_number)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Create new claim document for MongoDB
    from datetime import datetime
    from bson import ObjectId
    
    claim_doc = {
        "policy_number": claim.policy_number,
        "claim_type": claim.claim_type,
        "incident_date": claim.incident_date,
        "description": claim.description,
        "status": "pending",
        "fraud_score": None,
        "fraud_risk_level": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "documents": [],
        "questions_count": 0
    }
    
    # Insert into MongoDB
    result = db.claims.insert_one(claim_doc)
    claim_doc["_id"] = result.inserted_id
    
    return schemas.ClaimResponse(
        id=str(claim_doc["_id"]),
        policy_number=claim_doc["policy_number"],
        claim_type=claim_doc["claim_type"],
        incident_date=claim_doc["incident_date"].isoformat() if hasattr(claim_doc["incident_date"], 'isoformat') else claim_doc["incident_date"],
        description=claim_doc["description"],
        status=claim_doc["status"],
        fraud_score=claim_doc["fraud_score"],
        fraud_risk_level=claim_doc["fraud_risk_level"],
        created_at=claim_doc["created_at"].isoformat() if claim_doc["created_at"] else None,
        updated_at=claim_doc["updated_at"].isoformat() if claim_doc["updated_at"] else None,
        documents=[],
        questions_count=0
    )

@app.get("/api/claims/{claim_id}", response_model=schemas.ClaimResponse)
async def get_claim(claim_id: int, db = Depends(get_db)):
    """Get claim details by ID"""
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    documents = [{"id": d.id, "filename": d.filename, "document_type": d.document_type} for d in claim.documents]
    
    return schemas.ClaimResponse(
        id=str(claim.id),
        policy_number=claim.policy_number,
        claim_type=claim.claim_type,
        incident_date=claim.incident_date.isoformat(),
        description=claim.description,
        status=claim.status,
        fraud_score=claim.fraud_score,
        fraud_risk_level=claim.fraud_risk_level,
        created_at=claim.created_at.isoformat(),
        updated_at=claim.updated_at.isoformat(),
        documents=documents,
        questions_count=len(claim.questions)
    )

@app.get("/api/claims", response_model=schemas.ClaimsListResponse)
async def get_all_claims(
    policy_number: Optional[str] = None,
    status: Optional[str] = None,
    db = Depends(get_db)
):
    """Get all claims with optional filters"""
    query = db.query(models.Claim)
    
    if policy_number:
        query = query.filter(models.Claim.policy_number == policy_number)
    if status:
        query = query.filter(models.Claim.status == status)
    
    claims = query.all()
    
    claims_response = []
    for claim in claims:
        documents = [{"id": d.id, "filename": d.filename, "document_type": d.document_type} for d in claim.documents]
        claims_response.append(schemas.ClaimResponse(
            id=str(claim.id),
            policy_number=claim.policy_number,
            claim_type=claim.claim_type,
            incident_date=claim.incident_date.isoformat(),
            description=claim.description,
            status=claim.status,
            fraud_score=claim.fraud_score,
            fraud_risk_level=claim.fraud_risk_level,
            created_at=claim.created_at.isoformat(),
            updated_at=claim.updated_at.isoformat(),
            documents=documents,
            questions_count=len(claim.questions)
        ))
    
    return schemas.ClaimsListResponse(claims=claims_response, total=len(claims_response))

@app.get("/api/policies/{policy_number}/claims", response_model=schemas.ClaimsListResponse)
async def get_policy_claims(policy_number: str, db = Depends(get_db)):
    """Get all claims for a specific policy"""
    claims = db.query(models.Claim).filter(models.Claim.policy_number == policy_number).all()
    
    claims_response = []
    for claim in claims:
        documents = [{"id": d.id, "filename": d.filename, "document_type": d.document_type} for d in claim.documents]
        claims_response.append(schemas.ClaimResponse(
            id=str(claim.id),
            policy_number=claim.policy_number,
            claim_type=claim.claim_type,
            incident_date=claim.incident_date.isoformat(),
            description=claim.description,
            status=claim.status,
            fraud_score=claim.fraud_score,
            fraud_risk_level=claim.fraud_risk_level,
            created_at=claim.created_at.isoformat(),
            updated_at=claim.updated_at.isoformat(),
            documents=documents,
            questions_count=len(claim.questions)
        ))
    
    return schemas.ClaimsListResponse(claims=claims_response, total=len(claims_response))

# ==================== DOCUMENT ROUTES ====================

@app.post("/api/claims/{claim_id}/documents", response_model=schemas.DocumentUploadResponse)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str = "other",
    db = Depends(get_db)
):
    """Upload a document for a claim"""
    claim = db.claims.find_one({"_id": ObjectId(claim_id)})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Save file
    result = await document_service.upload_documentent(db, claim_id, file, document_type)
    
    return schemas.DocumentUploadResponse(
        id=result["id"],
        filename=result["filename"],
        document_type=result["document_type"],
        uploaded_at=result["uploaded_at"]
    )

# ==================== AI QUESTIONING ROUTES ====================

@app.post("/api/claims/{claim_id}/ask-question", response_model=schemas.QuestionResponse)
async def ask_question(
    claim_id: int,
    request: schemas.QuestionRequest,
    db = Depends(get_db)
):
    """AI asks questions about the claim"""
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get AI response
    response = await ai_service.ask_question(db, claim, request.user_message)
    
    return schemas.QuestionResponse(
        ai_message=response["ai_message"],
        follow_up_questions=response.get("follow_up_questions"),
        fraud_indicators=response.get("fraud_indicators")
    )

# ==================== FRAUD ANALYSIS ROUTES ====================

@app.post("/api/claims/{claim_id}/analyze-fraud", response_model=schemas.FraudAnalysisResponse)
async def analyze_fraud(claim_id: int, db = Depends(get_db)):
    """Perform fraud analysis on a claim"""
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Perform analysis
    result = await ai_service.analyze_fraud_risk(db, claim)
    
    # Update claim with fraud score
    claim.fraud_score = result["fraud_score"]
    claim.fraud_risk_level = result["risk_level"]
    db.commit()
    
    return schemas.FraudAnalysisResponse(
        fraud_score=result["fraud_score"],
        legit_percentage=result.get("legit_percentage"),
        risk_level=result["risk_level"],
        indicators=result["indicators"],
        recommendations=result["recommendations"],
        confidence=result["confidence"]
    )

# ==================== STATUS UPDATE ROUTES ====================

@app.patch("/api/claims/{claim_id}/status")
async def update_claim_status(
    claim_id: int,
    status_update: schemas.ClaimStatusUpdate,
    db = Depends(get_db)
):
    """Update claim status (admin)"""
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim.status = status_update.status
    db.commit()
    
    return {"message": "Status updated successfully", "status": claim.status}

# ==================== HEALTH CHECK ====================

@app.get("/")
async def root():
    return {"message": "Health Insurance Claim Portal API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
