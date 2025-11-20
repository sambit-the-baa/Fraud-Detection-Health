"""
Document Processor Service
Extracts and processes text from uploaded documents for fraud detection
"""
import os
import logging
from typing import Dict, List, Optional
import PyPDF2
import pdfplumber
from PIL import Image
import pytesseract
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes documents to extract text and features for fraud detection"""
    
    def __init__(self):
        # Configure Tesseract path if needed (Windows)
        if os.name == 'nt':
            # Common Tesseract installation paths on Windows
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text_content = []
            
            # Try pdfplumber first (better for structured documents)
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
            except Exception as e:
                logger.warning(f"pdfplumber failed for {file_path}: {e}, trying PyPDF2")
            
            # Fallback to PyPDF2
            if not text_content:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
            
            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {e}")
            return ""
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from document based on file type"""
        if file_type == 'application/pdf' or file_path.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_type.startswith('image/'):
            return self.extract_text_from_image(file_path)
        else:
            logger.warning(f"Unsupported file type for text extraction: {file_type}")
            return ""
    
    def extract_features(self, text: str, document_type: str) -> Dict:
        """Extract features from document text for fraud detection"""
        features = {
            'document_type': document_type,
            'text_length': len(text),
            'word_count': len(text.split()) if text else 0,
            'has_dates': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)),
            'has_amounts': bool(re.search(r'\$\d+\.?\d*|Rs\.?\s*\d+', text, re.IGNORECASE)),
            'has_phone_numbers': bool(re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', text)),
            'has_email': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
            'has_medical_terms': self._count_medical_terms(text),
            'has_prescription_terms': self._count_prescription_terms(text),
            'has_invoice_terms': self._count_invoice_terms(text),
            'date_consistency': self._check_date_consistency(text),
            'amount_consistency': self._check_amount_consistency(text),
            'has_signature': bool(re.search(r'signature|signed|authorized', text, re.IGNORECASE)),
            'has_stamp': bool(re.search(r'stamp|seal|official', text, re.IGNORECASE)),
            'has_doctor_name': bool(re.search(r'Dr\.|Doctor|Physician|MD|MBBS', text, re.IGNORECASE)),
            'has_hospital_name': bool(re.search(r'Hospital|Clinic|Medical Center|Healthcare', text, re.IGNORECASE)),
            'has_policy_number': bool(re.search(r'Policy|POL-|Policy No|Policy Number', text, re.IGNORECASE)),
            'has_claim_number': bool(re.search(r'Claim|CLM-|Claim No|Claim Number', text, re.IGNORECASE)),
        }
        
        return features
    
    def _count_medical_terms(self, text: str) -> int:
        """Count medical terminology in text"""
        medical_terms = [
            'diagnosis', 'treatment', 'symptom', 'disease', 'condition',
            'medication', 'prescription', 'dosage', 'therapy', 'surgery',
            'procedure', 'examination', 'test', 'result', 'patient'
        ]
        count = sum(1 for term in medical_terms if term.lower() in text.lower())
        return count
    
    def _count_prescription_terms(self, text: str) -> int:
        """Count prescription-related terms"""
        prescription_terms = [
            'prescription', 'rx', 'medication', 'drug', 'tablet', 'capsule',
            'dosage', 'frequency', 'duration', 'pharmacy', 'pharmacist'
        ]
        count = sum(1 for term in prescription_terms if term.lower() in text.lower())
        return count
    
    def _count_invoice_terms(self, text: str) -> int:
        """Count invoice/billing terms"""
        invoice_terms = [
            'invoice', 'bill', 'receipt', 'amount', 'total', 'charge',
            'payment', 'due', 'balance', 'tax', 'discount', 'subtotal'
        ]
        count = sum(1 for term in invoice_terms if term.lower() in text.lower())
        return count
    
    def _check_date_consistency(self, text: str) -> float:
        """Check if dates in document are consistent (0-1 score)"""
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)
        if len(dates) < 2:
            return 1.0  # Not enough dates to check consistency
        
        # Simple consistency check - dates should be in chronological order
        # This is a simplified check
        return 0.8  # Placeholder - can be enhanced
    
    def _check_amount_consistency(self, text: str) -> float:
        """Check if amounts in document are consistent (0-1 score)"""
        amounts = re.findall(r'\$\d+\.?\d*|Rs\.?\s*\d+', text, re.IGNORECASE)
        if len(amounts) < 2:
            return 1.0  # Not enough amounts to check
        
        # Simple consistency check
        return 0.8  # Placeholder - can be enhanced
    
    def process_document(self, file_path: str, document_type: str) -> Dict:
        """Process a document and return extracted text and features"""
        # Extract text
        text = self.extract_text(file_path, document_type)
        
        # Extract features
        features = self.extract_features(text, document_type)
        features['extracted_text'] = text[:1000]  # Store first 1000 chars for reference
        
        return {
            'text': text,
            'features': features
        }

