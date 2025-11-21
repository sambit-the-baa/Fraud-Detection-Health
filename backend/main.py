from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
import os
import logging
from dotenv import load_dotenv

# Import your other modules as needed (schemas, services, models)
from database import SessionLocal, engine, Base
# ... (other imports)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# Initialize app
app = FastAPI(title="Health Insurance Claim Portal", version="1.0.0")

# CORS middleware: Add allowed origins (your frontend domain!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fraud-detection-health-frontend.onrender.com",
        "http://localhost:3000",                # local dev
        "http://localhost:5173"                 # local dev (Vite)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your API route(s) come AFTER you create app!
@app.post("/api/verify-policy")
async def verify_policy(policy_data: dict, db: Session = Depends(get_db)):
    # Validate and respond (your real logic here)
    return {"result": "verified"}

# Add other `/api/...` endpoints as needed.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
