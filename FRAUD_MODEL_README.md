# Fraud Detection Model Documentation

## Overview

This fraud detection system uses machine learning to analyze uploaded health insurance claim documents and classify them as legitimate or fraudulent. The model processes PDF documents, extracts features, and provides a "Legit Percentage" score.

## Architecture

### Components

1. **Document Processor** (`backend/services/document_processor.py`)
   - Extracts text from PDFs and images using OCR
   - Extracts features from documents (dates, amounts, medical terms, etc.)
   - Validates document consistency

2. **Fraud Detection Model** (`backend/services/fraud_detection_model.py`)
   - Random Forest Classifier for fraud detection
   - Rule-based fallback when model is not trained
   - Provides legit percentage (0-100%)

3. **Training Script** (`backend/train_fraud_model.py`)
   - Processes training data from PDF files
   - Trains the ML model
   - Saves trained model for production use

## Features Extracted

The model analyzes documents for:

- **Document Structure**: Text length, word count, document type
- **Content Indicators**: Dates, amounts, phone numbers, emails
- **Medical Terms**: Presence of medical terminology
- **Verification Elements**: Signatures, stamps, doctor names, hospital names
- **Consistency Checks**: Date consistency, amount consistency
- **Policy Information**: Policy numbers, claim numbers

## Training the Model

### Step 1: Prepare Training Data

Place your PDF documents in the `Docs/Data/` directory. The training script will process all PDF files in this directory.

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- PyPDF2
- pdfplumber
- scikit-learn
- numpy
- pandas

### Step 3: Train the Model

```bash
cd backend
python train_fraud_model.py
```

Or specify a custom data directory:

```bash
python train_fraud_model.py "C:/Fraud detection/Docs/Data"
```

### Step 4: Model Output

The trained model will be saved to:
- `backend/models/fraud_detection_model.pkl`

## How It Works

1. **Document Upload**: User uploads documents through the portal
2. **Text Extraction**: Documents are processed to extract text
3. **Feature Extraction**: Features are extracted from the text
4. **Model Prediction**: ML model predicts legit percentage
5. **Risk Assessment**: Legit percentage is converted to fraud score and risk level
6. **Analysis Display**: Results shown in the fraud analysis page

## Legit Percentage Interpretation

- **70-100%**: Low Risk (Green) - Claim appears legitimate
- **40-70%**: Medium Risk (Yellow) - Requires review
- **0-40%**: High Risk (Red) - Potential fraud indicators

## Rule-Based Fallback

If the model is not trained, the system uses rule-based scoring:

- **Positive Indicators** (+points):
  - Has signature (+5)
  - Has stamp (+5)
  - Has doctor name (+5)
  - Has hospital name (+5)
  - Contains medical terms (+5)
  - Sufficient text length (+3)

- **Negative Indicators** (-points):
  - Very short documents (-10)
  - Missing dates (-5)
  - Missing amounts in invoices (-10)
  - Inconsistent dates (-10)
  - Inconsistent amounts (-10)

## Integration

The model is automatically integrated into the fraud analysis pipeline:

1. When a user completes AI questioning, documents are analyzed
2. The model processes all uploaded documents
3. Legit percentage is calculated
4. Results are displayed in the Fraud Analysis page

## Model Performance

The model uses:
- **Algorithm**: Random Forest Classifier
- **Features**: 18+ document features
- **Training**: Supervised learning on labeled data
- **Fallback**: Rule-based scoring when model unavailable

## Future Enhancements

- Add more training data for better accuracy
- Implement deep learning models
- Add document image analysis
- Cross-reference with policy database
- Real-time model retraining

## Troubleshooting

### Model Not Found
- The system will use rule-based scoring
- Train the model using `train_fraud_model.py`

### PDF Extraction Fails
- Check if PDF is password protected
- Verify PDF is not corrupted
- Try using different PDF library

### Low Accuracy
- Add more training data
- Review feature extraction logic
- Adjust model parameters
- Label training data more accurately

