# Backend API

FastAPI backend for the Health Insurance Claim Portal.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
DATABASE_URL=sqlite:///./insurance_claims.db
OPENAI_API_KEY=your_key_here
USE_GPT4=false
```

3. Seed database:
```bash
python seed_data.py
```

4. Run server:
```bash
python main.py
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

