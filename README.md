# Health Insurance Claim Portal

A comprehensive web application for processing health insurance claims with AI-powered fraud detection. Users can submit claims through a streamlined portal, upload necessary documents, and interact with an AI system that questions them about the claim to identify potential fraud cases.

## Features

- **Policy Verification**: Users enter their policy number to verify eligibility
- **Claim Submission**: Create and submit health insurance claims
- **Document Upload**: Upload medical reports, prescriptions, invoices, and other supporting documents
- **AI-Powered Questioning**: Interactive AI assistant asks relevant questions about the claim
- **Fraud Detection**: Automated fraud risk analysis with scoring and indicators
- **Modern UI**: Beautiful, responsive interface built with React and Tailwind CSS

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Database (can be upgraded to PostgreSQL)
- **Google Gemini API**: AI-powered fraud detection and questioning (with fallback mock responses)

### Frontend
- **React**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **React Router**: Navigation
- **Axios**: HTTP client

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the backend directory:
```env
DATABASE_URL=sqlite:///./insurance_claims.db
GEMINI_API_KEY=your_gemini_api_key_here
```

6. Seed the database with sample policies:
```bash
python seed_data.py
```

7. Run the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage Flow

1. **Policy Entry**: User enters policy number (e.g., `POL-2024-001`)
2. **Policy Verification**: System verifies the policy and displays policy holder information
3. **Dashboard Access**: User can view existing claims or create a new one
4. **Claim Creation**: User fills out claim form with incident details
5. **Document Upload**: User uploads relevant documents (medical reports, prescriptions, etc.)
6. **AI Questioning**: AI assistant asks questions about the claim to gather more information
7. **Fraud Analysis**: System performs comprehensive fraud risk analysis
8. **Success Page**: Confirmation of claim submission
9. **Claim Tracking**: User can view claim details and status anytime via dashboard

## API Endpoints

- `POST /api/verify-policy` - Verify policy number
- `POST /api/claims` - Create a new claim
- `GET /api/claims/{claim_id}` - Get detailed claim information
- `GET /api/policies/{policy_number}/claims` - Get all claims for a policy
- `GET /api/claims` - Get all claims (with optional filters)
- `POST /api/claims/{claim_id}/documents` - Upload documents
- `POST /api/claims/{claim_id}/ask-question` - AI questioning
- `POST /api/claims/{claim_id}/analyze-fraud` - Fraud risk analysis
- `PATCH /api/claims/{claim_id}/status` - Update claim status (admin)

## Sample Policy Numbers

After running `seed_data.py`, you can use these test policy numbers:
- `POL-2024-001`
- `POL-2024-002`
- `POL-2024-003`

## AI Configuration

The system uses Google's Gemini API for AI-powered features. If you don't have an API key, the system will use mock responses for testing purposes.

To enable full AI features:
1. Get a Gemini API key from https://makersuite.google.com/app/apikey
2. Add it to your `.env` file as `GEMINI_API_KEY=your_api_key_here`
3. The system will automatically use the Gemini Pro model for fraud detection

## Project Structure

```
.
├── backend/
│   ├── services/
│   │   ├── ai_service.py          # AI fraud detection logic
│   │   ├── document_service.py    # Document upload handling
│   │   └── policy_service.py      # Policy verification
│   ├── database.py                 # Database configuration
│   ├── models.py                   # SQLAlchemy models
│   ├── schemas.py                  # Pydantic schemas
│   ├── main.py                     # FastAPI application
│   ├── seed_data.py                # Database seeding script
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PolicyEntry.jsx     # Policy verification page
│   │   │   ├── Dashboard.jsx       # Claims dashboard
│   │   │   ├── ClaimForm.jsx       # Claim creation form
│   │   │   ├── ClaimDetails.jsx    # Claim details view
│   │   │   ├── ClaimSuccess.jsx    # Success confirmation page
│   │   │   ├── DocumentUpload.jsx  # Document upload interface
│   │   │   ├── AIQuestioning.jsx   # AI chat interface
│   │   │   └── FraudAnalysis.jsx   # Fraud analysis results
│   │   ├── api/
│   │   │   └── client.js           # API client
│   │   ├── App.jsx                 # Main app component
│   │   └── main.jsx                # Entry point
│   └── package.json                # Node dependencies
└── README.md
```

## Security Considerations

- Add authentication/authorization for production use
- Implement rate limiting
- Add input validation and sanitization
- Use environment variables for sensitive data
- Implement proper file upload security (size limits, file type validation)
- Add HTTPS in production
- Consider using a more robust database (PostgreSQL) for production

## Future Enhancements

- User authentication and accounts
- Email notifications
- Claim status tracking dashboard
- Advanced document OCR and analysis
- Integration with medical provider systems
- Real-time fraud alerts
- Admin dashboard for claim management
- Multi-language support

## License

This project is provided as-is for demonstration purposes.

