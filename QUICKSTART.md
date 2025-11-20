# Quick Start Guide

Get the Health Insurance Claim Portal up and running in minutes!

## Prerequisites Check

Make sure you have:
- Python 3.8+ installed
- Node.js 16+ installed
- npm or yarn installed

## Step-by-Step Setup

### 1. Backend Setup (Terminal 1)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy the example or create manually)
# Add your OpenAI API key if you have one (optional for testing)

# Seed database with sample policies
python seed_data.py

# Start the server
python main.py
```

Backend will run on `http://localhost:8000`

### 2. Frontend Setup (Terminal 2)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on `http://localhost:3000`

### 3. Test the Application

1. Open your browser and go to `http://localhost:3000`
2. Enter one of the test policy numbers:
   - `POL-2024-001`
   - `POL-2024-002`
   - `POL-2024-003`
3. Follow the flow:
   - Verify policy
   - Create claim
   - Upload documents
   - Answer AI questions
   - View fraud analysis

## Troubleshooting

### Backend Issues

- **Import errors**: Make sure virtual environment is activated and dependencies are installed
- **Database errors**: Delete `insurance_claims.db` and run `seed_data.py` again
- **Port already in use**: Change port in `main.py` or kill the process using port 8000

### Frontend Issues

- **Module not found**: Run `npm install` again
- **Port already in use**: Change port in `vite.config.js` or kill the process using port 3000
- **API connection errors**: Make sure backend is running on port 8000

### AI Features Not Working

- If you don't have a Gemini API key, the system will use mock responses
- To enable real AI features, add your Gemini API key to `backend/.env`:
  ```
  GEMINI_API_KEY=your-gemini-api-key-here
  ```
- Get your API key from: https://makersuite.google.com/app/apikey

## Next Steps

- Review the main README.md for detailed documentation
- Customize the AI prompts in `backend/services/ai_service.py`
- Add more sample policies in `backend/seed_data.py`
- Customize the UI in `frontend/src/components/`

## Need Help?

Check the main README.md for more detailed information about the project structure and features.

