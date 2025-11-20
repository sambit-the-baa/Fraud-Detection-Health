from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String, unique=True, index=True, nullable=False)
    policy_holder_name = Column(String, nullable=False)
    policy_type = Column(String, nullable=False)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    claims = relationship("Claim", back_populates="policy")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String, ForeignKey("policies.policy_number"), nullable=False)
    claim_type = Column(String, nullable=False)
    incident_date = Column(DateTime, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, under_review, approved, rejected
    fraud_score = Column(Float, default=0.0)
    fraud_risk_level = Column(String, default="low")  # low, medium, high
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    policy = relationship("Policy", back_populates="claims")
    documents = relationship("Document", back_populates="claim", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="claim", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String)  # medical_report, prescription, invoice, etc.
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    claim = relationship("Claim", back_populates="documents")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    user_message = Column(Text)
    ai_response = Column(Text)
    is_fraud_indicative = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    claim = relationship("Claim", back_populates="questions")

