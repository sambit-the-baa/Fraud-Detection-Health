import os
import json
import requests
import logging
from sqlalchemy.orm import Session
from models import Claim, Document, Question
from schemas import QuestionResponse, FraudAnalysisResponse
from typing import List, Optional
from dotenv import load_dotenv
from services.document_processor import DocumentProcessor
from services.fraud_detection_model import FraudDetectionModel

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Initialize Gemini API client
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        if self.api_key:
            self.enabled = True
            logger.info("Gemini API enabled")
        else:
            self.enabled = False
            logger.warning("GEMINI_API_KEY not set. AI features will use mock responses.")
        
        # Initialize document processor and fraud detection model
        self.document_processor = DocumentProcessor()
        self.fraud_model = FraudDetectionModel()
    
    async def ask_question(
        self,
        db: Session,
        claim: Claim,
        user_message: str,
        documents: List[Document],
        previous_questions: List[Question]
    ) -> QuestionResponse:
        """Generate AI question/response for fraud detection"""
        
        # Build context from claim and documents
        context = self._build_context(claim, documents, previous_questions)
        
        # Determine question number (1-based)
        question_number = len(previous_questions) + 1
        
        # Generate AI response
        if self.enabled:
            response = await self._generate_ai_response(context, user_message, previous_questions, question_number)
        else:
            response = self._generate_mock_response(user_message, claim, question_number)
        
        # Save question to database
        question = Question(
            claim_id=claim.id,
            user_message=user_message,
            ai_response=response["ai_message"],
            is_fraud_indicative=response.get("is_fraud_indicative", False)
        )
        db.add(question)
        db.commit()
        
        return QuestionResponse(
            ai_message=response["ai_message"],
            follow_up_questions=response.get("follow_up_questions", []),
            fraud_indicators=response.get("fraud_indicators", [])
        )
    
    async def analyze_fraud_risk(
        self,
        db: Session,
        claim: Claim,
        documents: List[Document],
        questions: List[Question]
    ) -> FraudAnalysisResponse:
        """Perform comprehensive fraud analysis using document processing and ML model"""
        
        # Process uploaded documents
        documents_features = []
        for doc in documents:
            try:
                if os.path.exists(doc.file_path):
                    result = self.document_processor.process_document(
                        doc.file_path,
                        doc.document_type or 'other'
                    )
                    documents_features.append(result['features'])
                    logger.info(f"Processed document {doc.id}: {doc.filename}")
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}")
        
        # Get legit percentage from ML model
        legit_percentage = self.fraud_model.predict_legit_percentage(documents_features)
        fraud_score = 100.0 - legit_percentage  # Convert to fraud score
        
        # Determine risk level
        if legit_percentage >= 70:
            risk_level = "low"
        elif legit_percentage >= 40:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Build context for AI analysis (if enabled)
        context = self._build_context(claim, documents, questions)
        
        # Get AI-generated indicators and recommendations
        if self.enabled:
            ai_analysis = await self._generate_fraud_analysis(context, claim, documents, questions)
            indicators = ai_analysis.get("indicators", [])
            recommendations = ai_analysis.get("recommendations", [])
            confidence = ai_analysis.get("confidence", 0.75)
        else:
            indicators = self._extract_indicators_from_features(documents_features, legit_percentage)
            recommendations = self._generate_recommendations(legit_percentage, documents_features)
            confidence = 0.75
        
        # Combine ML model results with AI analysis
        analysis = {
            "fraud_score": fraud_score,
            "legit_percentage": legit_percentage,
            "risk_level": risk_level,
            "indicators": indicators,
            "recommendations": recommendations,
            "confidence": confidence
        }
        
        # Update claim with fraud score
        claim.fraud_score = fraud_score
        claim.fraud_risk_level = risk_level
        db.commit()
        
        return FraudAnalysisResponse(**analysis)
    
    def _extract_indicators_from_features(self, documents_features: List[dict], legit_percentage: float) -> List[str]:
        """Extract fraud indicators from document features"""
        indicators = []
        
        if not documents_features:
            indicators.append("No documents uploaded for verification")
            return indicators
        
        for doc_features in documents_features:
            if doc_features.get('text_length', 0) < 50:
                indicators.append("Document contains very little text")
            if not doc_features.get('has_dates'):
                indicators.append("Missing dates in documents")
            if not doc_features.get('has_signature') and doc_features.get('document_type') in ['medical_report', 'prescription']:
                indicators.append("Missing signature on medical document")
            if not doc_features.get('has_doctor_name') and doc_features.get('document_type') == 'medical_report':
                indicators.append("Missing doctor information")
            if doc_features.get('date_consistency', 1.0) < 0.5:
                indicators.append("Inconsistent dates across documents")
            if doc_features.get('amount_consistency', 1.0) < 0.5:
                indicators.append("Inconsistent amounts across documents")
        
        if legit_percentage < 40:
            indicators.append("Low legitimacy score based on document analysis")
        
        return indicators if indicators else ["No major fraud indicators detected"]
    
    def _generate_recommendations(self, legit_percentage: float, documents_features: List[dict]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if legit_percentage < 40:
            recommendations.append("Conduct detailed manual review")
            recommendations.append("Request additional documentation")
            recommendations.append("Verify with medical providers")
        elif legit_percentage < 70:
            recommendations.append("Review documents carefully")
            recommendations.append("Cross-check policy coverage")
        else:
            recommendations.append("Standard review process")
            recommendations.append("Verify policy coverage")
        
        # Document-specific recommendations
        has_medical_report = any(d.get('document_type') == 'medical_report' for d in documents_features)
        has_invoice = any(d.get('document_type') == 'invoice' for d in documents_features)
        
        if not has_medical_report:
            recommendations.append("Request medical report for verification")
        if not has_invoice and any('invoice' in d.get('document_type', '') for d in documents_features):
            recommendations.append("Request itemized invoice")
        
        return recommendations
    
    def _build_context(
        self,
        claim: Claim,
        documents: List[Document],
        questions: List[Question]
    ) -> str:
        """Build context string for AI"""
        context_parts = [
            f"Claim Type: {claim.claim_type}",
            f"Incident Date: {claim.incident_date}",
            f"Description: {claim.description or 'No description provided'}",
            f"\nDocuments uploaded: {len(documents)}",
        ]
        
        for doc in documents:
            context_parts.append(f"- {doc.document_type}: {doc.filename}")
        
        if questions:
            context_parts.append("\nPrevious Q&A:")
            for q in questions[-5:]:  # Last 5 questions
                context_parts.append(f"Q: {q.user_message}")
                context_parts.append(f"A: {q.ai_response}")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(
        self,
        context: str,
        user_message: str,
        previous_questions: List[Question]
    ) -> dict:
        """Generate AI response using Google Gemini API"""
        # Determine question number
        question_num = len(previous_questions) + 1
        
        # Build contextual system prompt based on claim type and question number
        system_prompt = self._build_contextual_prompt(context, question_num)
        
        # Build conversation history
        conversation_text = f"{system_prompt}\n\nClaim Context:\n{context}\n\n"
        
        # Add previous conversation with question numbers
        start_num = question_num - len(previous_questions[-3:])
        for idx, q in enumerate(previous_questions[-3:], start=start_num):
            conversation_text += f"Question {idx} - User: {q.user_message}\n"
            conversation_text += f"Assistant: {q.ai_response}\n\n"
        
        conversation_text += f"Question {question_num} - User: {user_message}\n"
        conversation_text += "Assistant:"
        
        try:
            # Prepare Gemini API request
            payload = {
                "contents": [{
                    "parts": [{
                        "text": conversation_text
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make request to Gemini API
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract text from Gemini response
            if "candidates" in result and len(result["candidates"]) > 0:
                ai_message = result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                raise Exception("No response from Gemini API")
            
            # Analyze for fraud indicators
            fraud_indicators = self._extract_fraud_indicators(ai_message)
            
            return {
                "ai_message": ai_message,
                "follow_up_questions": self._extract_follow_ups(ai_message),
                "fraud_indicators": fraud_indicators,
                "is_fraud_indicative": len(fraud_indicators) > 0
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
            return self._generate_mock_response(user_message, None)
    
    async def _generate_fraud_analysis(
        self,
        context: str,
        claim: Claim,
        documents: List[Document],
        questions: List[Question]
    ) -> dict:
        """Generate comprehensive fraud analysis using Google Gemini API"""
        system_prompt = """You are an expert fraud analyst for health insurance claims.
        Analyze the claim comprehensively and provide:
        1. A fraud risk score (0-100)
        2. Risk level (low/medium/high)
        3. Specific fraud indicators found
        4. Recommendations for further action
        5. Confidence level in your assessment
        
        Be thorough and objective."""
        
        analysis_prompt = f"""{system_prompt}

Analyze this health insurance claim for fraud:

{context}

Provide your analysis in JSON format with:
- fraud_score: float (0-100)
- risk_level: string (low/medium/high)
- indicators: array of strings
- recommendations: array of strings
- confidence: float (0-1)

Respond with ONLY valid JSON, no additional text."""
        
        try:
            # Prepare Gemini API request
            payload = {
                "contents": [{
                    "parts": [{
                        "text": analysis_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1000
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make request to Gemini API
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract text from Gemini response
            if "candidates" in result and len(result["candidates"]) > 0:
                response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Try to extract JSON from response (might have markdown code blocks)
                response_text = response_text.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                analysis_result = json.loads(response_text)
                return analysis_result
            else:
                raise Exception("No response from Gemini API")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from Gemini: {str(e)}")
            logger.debug(f"Response text: {response_text if 'response_text' in locals() else 'N/A'}")
            return self._generate_mock_fraud_analysis(claim, documents, questions)
        except Exception as e:
            logger.error(f"Error in fraud analysis: {str(e)}", exc_info=True)
            return self._generate_mock_fraud_analysis(claim, documents, questions)
    
    def _generate_mock_response(self, user_message: str, claim: Optional[Claim], question_number: int = 1) -> dict:
        """Generate mock response when AI is not available"""
        # Contextual responses based on question number
        if question_number == 1:
            if claim and "hospitalization" in claim.claim_type.lower():
                response = "Can you please tell me when you were admitted to the hospital and what was the primary reason for your admission?"
            elif claim and "emergency" in claim.claim_type.lower():
                response = "Can you describe what happened during the emergency incident? When did it occur?"
            else:
                response = "Can you please provide more details about when the incident occurred and what happened?"
        elif question_number == 2:
            response = "Thank you for that information. Can you tell me about the medical providers involved? Who was your treating physician?"
        elif question_number == 3:
            response = "I appreciate the details. Can you provide the contact information of the treating physician or hospital for verification purposes?"
        else:
            response = "Thank you for all the information. I have enough details now to proceed with the analysis."
        
        return {
            "ai_message": response,
            "follow_up_questions": [],
            "fraud_indicators": [],
            "is_fraud_indicative": False
        }
    
    def _generate_mock_fraud_analysis(
        self,
        claim: Claim,
        documents: List[Document],
        questions: List[Question]
    ) -> dict:
        """Generate mock fraud analysis"""
        # Simple heuristic-based scoring
        score = 25.0  # Base score
        indicators = []
        
        if len(documents) < 2:
            score += 10
            indicators.append("Insufficient documentation")
        
        if len(questions) < 3:
            score += 5
            indicators.append("Limited questioning completed")
        
        risk_level = "low"
        if score > 50:
            risk_level = "high"
        elif score > 30:
            risk_level = "medium"
        
        return {
            "fraud_score": min(score, 100.0),
            "risk_level": risk_level,
            "indicators": indicators,
            "recommendations": [
                "Review all submitted documents carefully",
                "Verify with medical providers",
                "Cross-check policy coverage"
            ],
            "confidence": 0.75
        }
    
    def _extract_fraud_indicators(self, text: str) -> List[str]:
        """Extract potential fraud indicators from AI response"""
        indicators = []
        text_lower = text.lower()
        
        fraud_keywords = {
            "inconsistency": "Inconsistent information",
            "suspicious": "Suspicious pattern detected",
            "unusual": "Unusual circumstances",
            "delay": "Unexplained delay",
            "missing": "Missing documentation"
        }
        
        for keyword, indicator in fraud_keywords.items():
            if keyword in text_lower:
                indicators.append(indicator)
        
        return indicators
    
    def _build_contextual_prompt(self, context: str, question_num: int) -> str:
        """Build contextual prompt based on claim type and question number"""
        base_prompt = """You are a fraud detection specialist for health insurance claims. 
        Your role is to ask insightful, contextual questions to identify potential fraud indicators.
        Be professional, empathetic, but thorough. Look for inconsistencies, suspicious patterns,
        or red flags."""
        
        # Extract claim type from context
        claim_type = ""
        if "Claim Type:" in context:
            claim_type = context.split("Claim Type:")[1].split("\n")[0].strip()
        
        # Question-specific prompts
        if question_num == 1:
            if "hospitalization" in claim_type.lower() or "surgery" in claim_type.lower():
                return f"""{base_prompt}
                
                This is question 1 of 3-4 questions. Focus on gathering basic incident details.
                Ask about: admission date, primary reason, hospital name, treating physician.
                Keep the question focused and specific to hospitalization/surgery."""
            elif "emergency" in claim_type.lower():
                return f"""{base_prompt}
                
                This is question 1 of 3-4 questions. Focus on the emergency incident.
                Ask about: when it happened, what happened, where it occurred, immediate actions taken.
                Keep the question focused on emergency details."""
            elif "prescription" in claim_type.lower():
                return f"""{base_prompt}
                
                This is question 1 of 3-4 questions. Focus on the prescription details.
                Ask about: medication name, prescribing doctor, condition being treated, date prescribed.
                Keep the question focused on prescription information."""
            else:
                return f"""{base_prompt}
                
                This is question 1 of 3-4 questions. Focus on gathering basic incident information.
                Ask about: when the incident occurred, what happened, where it happened.
                Keep the question focused and specific."""
        
        elif question_num == 2:
            return f"""{base_prompt}
            
            This is question 2 of 3-4 questions. Now dig deeper into the circumstances.
            Ask about: timeline details, witnesses, medical providers involved, documentation.
            Look for any inconsistencies with the first answer."""
        
        elif question_num == 3:
            return f"""{base_prompt}
            
            This is question 3 of 3-4 questions. Focus on verification and validation.
            Ask about: contact information for medical providers, any delays in seeking treatment,
            previous similar claims, or any unusual circumstances.
            This may be your last question, so make it count."""
        
        else:  # question_num >= 4
            return f"""{base_prompt}
            
            This is question {question_num}. You should wrap up soon.
            Ask a final clarifying question if needed, or thank them and indicate you have enough information.
            Focus on any remaining gaps or inconsistencies."""
    
    def _extract_follow_ups(self, text: str) -> List[str]:
        """Extract follow-up questions from AI response"""
        # Simple extraction - look for question marks
        sentences = text.split('.')
        questions = [s.strip() + '?' for s in sentences if '?' in s]
        return questions[:3]  # Return up to 3 follow-up questions

