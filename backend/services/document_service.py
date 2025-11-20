import os
import uuid
import mimetypes
from sqlalchemy.orm import Session
from models import Document
from fastapi import UploadFile, HTTPException
from typing import Optional
import aiofiles

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DocumentService:
    def _validate_file(self, file: UploadFile) -> None:
        """Validate file size, type, and extension"""
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check MIME type
        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File MIME type not allowed: {file.content_type}"
            )
    
    async def upload_document(
        self,
        db: Session,
        claim_id: int,
        file: UploadFile,
        document_type: Optional[str] = None
    ) -> Document:
        """Upload and save a document with validation"""
        # Validate file
        self._validate_file(file)
        
        # Read file content
        content = await file.read()
        
        # Check file size
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Create claim-specific directory
        claim_dir = os.path.join(UPLOAD_DIR, f"claim_{claim_id}")
        os.makedirs(claim_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(claim_dir, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Determine document type if not provided
        if not document_type:
            document_type = self._infer_document_type(file.filename)
        
        # Create database record
        document = Document(
            claim_id=claim_id,
            filename=file.filename,
            document_type=document_type,
            file_path=file_path,
            file_size=file_size
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document
    
    def _infer_document_type(self, filename: str) -> str:
        """Infer document type from filename"""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ['medical', 'report', 'diagnosis']):
            return "medical_report"
        elif any(keyword in filename_lower for keyword in ['prescription', 'rx']):
            return "prescription"
        elif any(keyword in filename_lower for keyword in ['invoice', 'bill', 'receipt']):
            return "invoice"
        elif any(keyword in filename_lower for keyword in ['lab', 'test', 'result']):
            return "lab_result"
        else:
            return "other"

