# How to Access the Portal

## Frontend (User Interface)
**Open in your browser:**
```
http://localhost:3000
```

This is the main portal where you can:
- Enter policy numbers
- Submit claims
- Upload documents
- Interact with AI
- View fraud analysis

## Backend API (For Developers)
**API Documentation:**
```
http://localhost:8000/docs
```

**API Root:**
```
http://localhost:8000
```
(This only shows a JSON message - not the full portal)

## Quick Start

1. **Open your web browser**
2. **Navigate to:** `http://localhost:3000`
3. **Enter a test policy number:**
   - `POL-2024-001`
   - `POL-2024-002`
   - `POL-2024-003`

## Troubleshooting

If you see only JSON:
- You're accessing the API endpoint (`http://localhost:8000`)
- Use the frontend URL instead: `http://localhost:3000`

If the frontend doesn't load:
- Check that both servers are running
- Backend should be on port 8000
- Frontend should be on port 3000

