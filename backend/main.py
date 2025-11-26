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
from datetime import datetime

# Import your other modules
from database import get_sync_db
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
