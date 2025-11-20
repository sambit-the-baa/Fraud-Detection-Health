import os
import json
import requests
import logging
from sqlalchemy.orm import Session
from models import Claim, Document, Question
from schemas import QuestionResponse, FraudAnalysisResponse
from typing import List, Optional
from dotenv import load_dotenv

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
        
        # Generate AI response
        if self.enabled:
            response = await self._generate_ai_response(context, user_message, previous_questions)
        else:
            response = self._generate_mock_response(user_message, claim)
        
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
        """Perform comprehensive fraud analysis"""
        
        context = self._build_context(claim, documents, questions)
        
        if self.enabled:
            analysis = await self._generate_fraud_analysis(context, claim, documents, questions)
        else:
            analysis = self._generate_mock_fraud_analysis(claim, documents, questions)
        
        # Update claim with fraud score
        claim.fraud_score = analysis["fraud_score"]
        claim.fraud_risk_level = analysis["risk_level"]
        db.commit()
        
        return FraudAnalysisResponse(**analysis)
    
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
        system_prompt = """You are a fraud detection specialist for health insurance claims. 
        Your role is to ask insightful questions to identify potential fraud indicators.
        Be professional, empathetic, but thorough. Look for inconsistencies, suspicious patterns,
        or red flags. Ask follow-up questions when needed."""
        
        # Build conversation history
        conversation_text = f"{system_prompt}\n\nClaim Context:\n{context}\n\n"
        
        # Add previous conversation
        for q in previous_questions[-3:]:
            conversation_text += f"User: {q.user_message}\n"
            conversation_text += f"Assistant: {q.ai_response}\n\n"
        
        conversation_text += f"User: {user_message}\n"
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
    
    def _generate_mock_response(self, user_message: str, claim: Optional[Claim]) -> dict:
        """Generate mock response when AI is not available"""
        responses = [
            "Thank you for that information. Can you please provide more details about when the symptoms first appeared?",
            "I understand. Could you clarify the sequence of events leading up to the incident?",
            "That's helpful. Are there any witnesses or medical professionals who can corroborate this information?",
            "Thank you. Can you explain why there was a delay between the incident and seeking medical attention?",
            "I see. Could you provide the contact information of the treating physician for verification?"
        ]
        
        import random
        return {
            "ai_message": random.choice(responses),
            "follow_up_questions": [
                "When did the symptoms first appear?",
                "Who was the treating physician?"
            ],
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
    
    def _extract_follow_ups(self, text: str) -> List[str]:
        """Extract follow-up questions from AI response"""
        # Simple extraction - look for question marks
        sentences = text.split('.')
        questions = [s.strip() + '?' for s in sentences if '?' in s]
        return questions[:3]  # Return up to 3 follow-up questions

