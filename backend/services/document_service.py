import os
import uuid
import mimetypes
import base64
import hashlib
from datetime import datetime
from fastapi import UploadFile, HTTPException
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging

# MongoDB imports
from database import get_sync_db, get_async_db

logger = logging.getLogger(__name__)

# Configuration
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

# Simple text extraction for generating embeddings
def extract_text_from_document(content: bytes, filename: str, mime_type: str) -> str:
    """Extract text content from document for embedding generation."""
    try:
        # For PDFs, try to extract text
        if mime_type == 'application/pdf':
            try:
                import PyPDF2
                from io import BytesIO
                pdf_file = BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                return text[:5000] if text else filename  # Limit to 5000 chars
            except Exception as e:
                logger.warning(f"Could not extract PDF text: {e}")
                return filename
        
        # For images, return filename and metadata
        elif mime_type.startswith('image/'):
            return f"Image document: {filename}"
        
        # For Word documents
        elif 'wordprocessingml' in mime_type or mime_type == 'application/msword':
            try:
                from docx import Document
                from io import BytesIO
                doc = Document(BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs])
                return text[:5000] if text else filename
            except Exception as e:
                logger.warning(f"Could not extract Word text: {e}")
                return filename
        
        return filename
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return filename


def generate_simple_embedding(text: str) -> List[float]:
    """Generate a simple embedding vector using hash-based approach.
    
    This creates a deterministic 128-dimensional vector from text.
    For production, replace with sentence-transformers or OpenAI embeddings.
    """
    # Create a simple hash-based embedding
    # This is a placeholder - in production use sentence-transformers
    import hashlib
    
    # Normalize text
    text = text.lower().strip()
    
    # Generate 128-dimensional embedding using multiple hash functions
    embedding = []
    for i in range(128):
        hash_input = f"{text}_{i}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        # Normalize to [-1, 1]
        normalized = (hash_value % 10000) / 5000 - 1
        embedding.append(normalized)
    
    return embedding


class DocumentService:
    """Document service using MongoDB for storage with vector embeddings."""
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate file size, type, and extension."""
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
        db,
        claim_id: str,
        file: UploadFile,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload and save a document with vector embedding to MongoDB."""
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
        
        # Generate unique document ID
        doc_id = str(ObjectId())
        
        # Determine document type if not provided
        if not document_type:
            document_type = self._infer_document_type(file.filename)
        
        # Get MIME type
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        # Extract text for embedding
        text_content = extract_text_from_document(content, file.filename, mime_type)
        
        # Generate vector embedding
        embedding = generate_simple_embedding(text_content)
        
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Encode content as base64 for storage
        content_base64 = base64.b64encode(content).decode('utf-8')
        
        # Create document record
        document_doc = {
            "_id": ObjectId(doc_id),
            "claim_id": claim_id,
            "filename": file.filename,
            "document_type": document_type,
            "mime_type": mime_type,
            "file_size": file_size,
            "file_hash": file_hash,
            "content": content_base64,
            "text_content": text_content[:2000],  # Store truncated text for reference
            "embedding": embedding,
            "uploaded_at": datetime.utcnow(),
            "status": "active"
        }
        
        # Insert into MongoDB
        result = db.documents.insert_one(document_doc)
        
        logger.info(f"Document uploaded: {doc_id} for claim {claim_id}")
        
        return {
            "id": doc_id,
            "claim_id": claim_id,
            "filename": file.filename,
            "document_type": document_type,
            "file_size": file_size,
            "mime_type": mime_type,
            "uploaded_at": document_doc["uploaded_at"].isoformat(),
            "has_embedding": True
        }
    
    def get_documents_by_claim(self, db, claim_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific claim."""
        documents = db.documents.find({"claim_id": claim_id, "status": "active"})
        
        result = []
        for doc in documents:
            result.append({
                "id": str(doc["_id"]),
                "claim_id": doc["claim_id"],
                "filename": doc["filename"],
                "document_type": doc["document_type"],
                "file_size": doc["file_size"],
                "mime_type": doc.get("mime_type", "application/octet-stream"),
                "uploaded_at": doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None,
                "has_embedding": "embedding" in doc
            })
        
        return result
    
    def get_document_by_id(self, db, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        try:
            doc = db.documents.find_one({"_id": ObjectId(document_id)})
            if not doc:
                return None
            
            return {
                "id": str(doc["_id"]),
                "claim_id": doc["claim_id"],
                "filename": doc["filename"],
                "document_type": doc["document_type"],
                "file_size": doc["file_size"],
                "mime_type": doc.get("mime_type", "application/octet-stream"),
                "content": doc.get("content"),  # Base64 encoded
                "uploaded_at": doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None,
                "has_embedding": "embedding" in doc
            }
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    def search_similar_documents(
        self,
        db,
        query_text: str,
        claim_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.
        
        This uses a simple cosine similarity calculation.
        For production with MongoDB Atlas, use $vectorSearch aggregation.
        """
        # Generate embedding for query
        query_embedding = generate_simple_embedding(query_text)
        
        # Build filter
        filter_query = {"status": "active"}
        if claim_id:
            filter_query["claim_id"] = claim_id
        
        # Get all documents with embeddings
        documents = list(db.documents.find(filter_query))
        
        # Calculate similarity scores
        results = []
        for doc in documents:
            if "embedding" in doc:
                # Calculate cosine similarity
                doc_embedding = doc["embedding"]
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                
                results.append({
                    "id": str(doc["_id"]),
                    "claim_id": doc["claim_id"],
                    "filename": doc["filename"],
                    "document_type": doc["document_type"],
                    "similarity_score": similarity,
                    "text_preview": doc.get("text_content", "")[:200]
                })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def delete_document(self, db, document_id: str) -> bool:
        """Soft delete a document."""
        try:
            result = db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"status": "deleted", "deleted_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def _infer_document_type(self, filename: str) -> str:
        """Infer document type from filename."""
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


# Create singleton instance
document_service = DocumentService()
