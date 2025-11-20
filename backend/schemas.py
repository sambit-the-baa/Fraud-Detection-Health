from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class PolicyVerificationRequest(BaseModel):
    policy_number: str = Field(..., min_length=1, max_length=50, description="Policy number to verify")
    
    @validator('policy_number')
    def validate_policy_number(cls, v):
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Policy number contains invalid characters')
        return v.strip()

class PolicyVerificationResponse(BaseModel):
    valid: bool
    policy_number: str
    policy_holder_name: str
    policy_type: str
    expiry_date: Optional[str] = None

class ClaimCreate(BaseModel):
    policy_number: str = Field(..., min_length=1, max_length=50)
    claim_type: str = Field(..., min_length=1, max_length=100)
    incident_date: datetime
    description: Optional[str] = Field(None, max_length=5000)
    
    @validator('policy_number')
    def validate_policy_number(cls, v):
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Policy number contains invalid characters')
        return v.strip()
    
    @validator('claim_type')
    def validate_claim_type(cls, v):
        allowed_types = [
            'Medical Treatment', 'Hospitalization', 'Surgery',
            'Emergency', 'Prescription', 'Other'
        ]
        if v not in allowed_types:
            raise ValueError(f'Claim type must be one of: {", ".join(allowed_types)}')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v:
            # Remove potentially dangerous characters
            v = re.sub(r'<[^>]+>', '', v)  # Remove HTML tags
            return v.strip()
        return v

class ClaimResponse(BaseModel):
    id: int
    policy_number: str
    claim_type: str
    incident_date: str
    status: str
    created_at: str
    fraud_score: Optional[float] = None
    fraud_risk_level: Optional[str] = None

class ClaimDetailResponse(BaseModel):
    id: int
    policy_number: str
    claim_type: str
    incident_date: str
    description: Optional[str] = None
    status: str
    fraud_score: Optional[float] = None
    fraud_risk_level: Optional[str] = None
    created_at: str
    updated_at: str
    documents: List[dict] = []
    questions_count: int = 0

class ClaimsListResponse(BaseModel):
    claims: List[ClaimResponse]
    total: int

class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    uploaded_at: str

class QuestionRequest(BaseModel):
    user_message: str

class QuestionResponse(BaseModel):
    ai_message: str
    follow_up_questions: Optional[List[str]] = None
    fraud_indicators: Optional[List[str]] = None

class FraudAnalysisResponse(BaseModel):
    fraud_score: float
    risk_level: str
    indicators: List[str]
    recommendations: List[str]
    confidence: float

class ClaimStatusUpdate(BaseModel):
    status: str  # pending, under_review, approved, rejected
    notes: Optional[str] = None
