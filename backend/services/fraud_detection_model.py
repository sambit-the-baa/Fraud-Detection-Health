"""
Fraud Detection Model
Machine learning model for classifying health insurance claims as fraud or legit
"""
import os
import pickle
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pandas as pd

logger = logging.getLogger(__name__)

class FraudDetectionModel:
    """Machine learning model for fraud detection"""
    
    def __init__(self, model_path: str = "models/fraud_detection_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'text_length', 'word_count', 'has_dates', 'has_amounts',
            'has_phone_numbers', 'has_email', 'has_medical_terms',
            'has_prescription_terms', 'has_invoice_terms', 'date_consistency',
            'amount_consistency', 'has_signature', 'has_stamp',
            'has_doctor_name', 'has_hospital_name', 'has_policy_number',
            'has_claim_number'
        ]
        self.document_type_encoding = {
            'medical_report': 1.0,
            'prescription': 0.8,
            'invoice': 0.6,
            'lab_result': 0.7,
            'other': 0.5
        }
        
        # Load model if it exists
        self.load_model()
    
    def _extract_features_vector(self, features: Dict) -> np.ndarray:
        """Convert features dictionary to feature vector"""
        feature_vector = []
        
        # Document type encoding
        doc_type = features.get('document_type', 'other')
        doc_type_value = self.document_type_encoding.get(doc_type, 0.5)
        feature_vector.append(doc_type_value)
        
        # Extract all numeric features
        for feature_name in self.feature_names:
            value = features.get(feature_name, 0)
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            feature_vector.append(float(value))
        
        return np.array(feature_vector).reshape(1, -1)
    
    def predict_legit_percentage(self, documents_features: List[Dict]) -> float:
        """
        Predict the legit percentage for a claim based on document features
        
        Args:
            documents_features: List of feature dictionaries from processed documents
            
        Returns:
            float: Legit percentage (0-100)
        """
        if not documents_features:
            return 50.0  # Default to uncertain if no documents
        
        if self.model is None:
            # Use rule-based scoring if model not trained
            return self._rule_based_scoring(documents_features)
        
        try:
            # Aggregate features from all documents
            aggregated_features = self._aggregate_features(documents_features)
            
            # Extract feature vector
            feature_vector = self._extract_features_vector(aggregated_features)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict probability
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(feature_vector_scaled)[0]
                # Assuming class 0 is fraud, class 1 is legit
                legit_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                # Binary prediction
                prediction = self.model.predict(feature_vector_scaled)[0]
                legit_probability = 1.0 if prediction == 1 else 0.0
            
            # Convert to percentage
            legit_percentage = legit_probability * 100
            
            return max(0.0, min(100.0, legit_percentage))
        except Exception as e:
            logger.error(f"Error in model prediction: {e}")
            return self._rule_based_scoring(documents_features)
    
    def _aggregate_features(self, documents_features: List[Dict]) -> Dict:
        """Aggregate features from multiple documents"""
        aggregated = {
            'document_type': 'mixed',
            'text_length': 0,
            'word_count': 0,
            'has_dates': False,
            'has_amounts': False,
            'has_phone_numbers': False,
            'has_email': False,
            'has_medical_terms': 0,
            'has_prescription_terms': 0,
            'has_invoice_terms': 0,
            'date_consistency': 1.0,
            'amount_consistency': 1.0,
            'has_signature': False,
            'has_stamp': False,
            'has_doctor_name': False,
            'has_hospital_name': False,
            'has_policy_number': False,
            'has_claim_number': False,
        }
        
        for doc_features in documents_features:
            # Sum numeric features
            aggregated['text_length'] += doc_features.get('text_length', 0)
            aggregated['word_count'] += doc_features.get('word_count', 0)
            aggregated['has_medical_terms'] += doc_features.get('has_medical_terms', 0)
            aggregated['has_prescription_terms'] += doc_features.get('has_prescription_terms', 0)
            aggregated['has_invoice_terms'] += doc_features.get('has_invoice_terms', 0)
            
            # OR boolean features
            aggregated['has_dates'] = aggregated['has_dates'] or doc_features.get('has_dates', False)
            aggregated['has_amounts'] = aggregated['has_amounts'] or doc_features.get('has_amounts', False)
            aggregated['has_phone_numbers'] = aggregated['has_phone_numbers'] or doc_features.get('has_phone_numbers', False)
            aggregated['has_email'] = aggregated['has_email'] or doc_features.get('has_email', False)
            aggregated['has_signature'] = aggregated['has_signature'] or doc_features.get('has_signature', False)
            aggregated['has_stamp'] = aggregated['has_stamp'] or doc_features.get('has_stamp', False)
            aggregated['has_doctor_name'] = aggregated['has_doctor_name'] or doc_features.get('has_doctor_name', False)
            aggregated['has_hospital_name'] = aggregated['has_hospital_name'] or doc_features.get('has_hospital_name', False)
            aggregated['has_policy_number'] = aggregated['has_policy_number'] or doc_features.get('has_policy_number', False)
            aggregated['has_claim_number'] = aggregated['has_claim_number'] or doc_features.get('has_claim_number', False)
            
            # Average consistency scores
            date_consistency = doc_features.get('date_consistency', 1.0)
            amount_consistency = doc_features.get('amount_consistency', 1.0)
            aggregated['date_consistency'] = (aggregated['date_consistency'] + date_consistency) / 2
            aggregated['amount_consistency'] = (aggregated['amount_consistency'] + amount_consistency) / 2
        
        return aggregated
    
    def _rule_based_scoring(self, documents_features: List[Dict]) -> float:
        """Rule-based scoring when model is not available"""
        if not documents_features:
            return 50.0
        
        score = 50.0  # Start with neutral
        
        # Positive indicators (increase legit score)
        for doc_features in documents_features:
            if doc_features.get('has_signature'):
                score += 5
            if doc_features.get('has_stamp'):
                score += 5
            if doc_features.get('has_doctor_name'):
                score += 5
            if doc_features.get('has_hospital_name'):
                score += 5
            if doc_features.get('has_policy_number'):
                score += 3
            if doc_features.get('has_claim_number'):
                score += 3
            if doc_features.get('has_medical_terms', 0) > 3:
                score += 5
            if doc_features.get('text_length', 0) > 500:
                score += 3
        
        # Negative indicators (decrease legit score)
        for doc_features in documents_features:
            if doc_features.get('text_length', 0) < 50:
                score -= 10  # Very short documents are suspicious
            if not doc_features.get('has_dates'):
                score -= 5  # Missing dates
            if not doc_features.get('has_amounts') and doc_features.get('document_type') == 'invoice':
                score -= 10  # Invoice without amounts
            if doc_features.get('date_consistency', 1.0) < 0.5:
                score -= 10  # Inconsistent dates
            if doc_features.get('amount_consistency', 1.0) < 0.5:
                score -= 10  # Inconsistent amounts
        
        # Normalize to 0-100
        score = max(0.0, min(100.0, score))
        
        return score
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """Train the fraud detection model"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            logger.info(f"Model trained - Train accuracy: {train_score:.2f}, Test accuracy: {test_score:.2f}")
            
            return train_score, test_score
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def save_model(self):
        """Save the trained model"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names
                }, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load a trained model"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.feature_names = data.get('feature_names', self.feature_names)
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.info("No trained model found, using rule-based scoring")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None

