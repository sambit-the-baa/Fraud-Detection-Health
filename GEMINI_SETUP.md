# Gemini API Setup

The portal now uses Google's Gemini API for AI-powered fraud detection and questioning.

## Getting Your API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

## Configuration

Add your Gemini API key to `backend/.env`:

```env
DATABASE_URL=sqlite:///./insurance_claims.db
GEMINI_API_KEY=your_api_key_here
```

## Restart Required

After adding your API key, restart the backend server:

1. Stop the current backend server (Ctrl+C in the terminal)
2. Restart it:
   ```bash
   cd backend
   .\venv\Scripts\Activate.ps1  # Windows
   python main.py
   ```

## API Endpoint

The system uses the Gemini Pro model via:
```
https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
```

## Testing

- Without API key: The system will use mock responses (still functional for testing)
- With API key: Full AI-powered fraud detection and questioning

## Features Using Gemini

1. **Interactive Questioning**: AI asks relevant questions about the claim
2. **Fraud Analysis**: Comprehensive fraud risk scoring and indicators
3. **Context Awareness**: AI considers claim details, documents, and conversation history

