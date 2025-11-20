"""
Training Script for Fraud Detection Model
Processes PDF documents from Docs/Data directory and trains the model
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.document_processor import DocumentProcessor
from services.fraud_detection_model import FraudDetectionModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_training_documents(data_dir: str) -> tuple:
    """
    Process all PDF documents in the training data directory
    
    Returns:
        tuple: (features_list, labels_list) - features and labels for training
    """
    processor = DocumentProcessor()
    features_list = []
    labels_list = []
    
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return [], []
    
    pdf_files = list(data_path.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {data_dir}")
    
    if len(pdf_files) == 0:
        logger.warning("No PDF files found for training")
        return [], []
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing {pdf_file.name}...")
            
            # Process document
            result = processor.process_document(str(pdf_file), 'medical_report')
            features = result['features']
            
            # For now, we'll use rule-based labeling
            # In a real scenario, you would have labeled data
            # This is a heuristic approach - you can manually label or use other methods
            label = _infer_label_from_features(features, pdf_file.name)
            
            features_list.append(features)
            labels_list.append(label)
            
            logger.info(f"  - Extracted {features.get('word_count', 0)} words")
            logger.info(f"  - Label: {'LEGIT' if label == 1 else 'FRAUD'}")
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(features_list)} documents")
    return features_list, labels_list

def _infer_label_from_features(features: dict, filename: str) -> int:
    """
    Infer label from features (heuristic approach)
    In production, you would have actual labeled data
    
    Returns:
        int: 1 for legit, 0 for fraud
    """
    score = 0
    
    # Positive indicators
    if features.get('has_signature'):
        score += 2
    if features.get('has_stamp'):
        score += 2
    if features.get('has_doctor_name'):
        score += 2
    if features.get('has_hospital_name'):
        score += 2
    if features.get('has_medical_terms', 0) > 5:
        score += 2
    if features.get('text_length', 0) > 500:
        score += 1
    if features.get('has_dates'):
        score += 1
    if features.get('has_amounts'):
        score += 1
    
    # Negative indicators
    if features.get('text_length', 0) < 100:
        score -= 3
    if not features.get('has_dates'):
        score -= 2
    if features.get('date_consistency', 1.0) < 0.5:
        score -= 2
    
    # Threshold: score >= 3 is legit, else fraud
    # This is a heuristic - adjust based on your data
    return 1 if score >= 3 else 0

def prepare_training_data(features_list: list, labels_list: list) -> tuple:
    """Convert features to numpy arrays for training"""
    model = FraudDetectionModel()
    
    X = []
    y = np.array(labels_list)
    
    for features in features_list:
        feature_vector = model._extract_features_vector(features)
        X.append(feature_vector[0])
    
    X = np.array(X)
    
    return X, y

def train_model(data_dir: str = "Docs/Data", model_save_path: str = "models/fraud_detection_model.pkl"):
    """Main training function"""
    logger.info("Starting fraud detection model training...")
    
    # Process documents
    features_list, labels_list = process_training_documents(data_dir)
    
    if len(features_list) == 0:
        logger.warning("No training data available. Model will use rule-based scoring.")
        return
    
    # Prepare training data
    logger.info("Preparing training data...")
    X, y = prepare_training_data(features_list, labels_list)
    
    # Check class distribution
    unique, counts = np.unique(y, return_counts=True)
    logger.info(f"Class distribution: {dict(zip(unique, counts))}")
    
    # Train model
    logger.info("Training model...")
    model = FraudDetectionModel(model_path=model_save_path)
    
    try:
        train_score, test_score = model.train(X, y)
        logger.info(f"Training completed!")
        logger.info(f"  Train Accuracy: {train_score:.2%}")
        logger.info(f"  Test Accuracy: {test_score:.2%}")
        
        # Save model
        model.save_model()
        logger.info(f"Model saved to {model_save_path}")
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        logger.info("Model will use rule-based scoring until training data is available")

if __name__ == "__main__":
    # Get data directory from command line or use default
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "Docs/Data"
    
    # Convert to absolute path
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), data_dir)
    
    train_model(data_dir)

