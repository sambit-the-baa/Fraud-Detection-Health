# Troubleshooting: "Policy Not Found" Error

## Quick Fix

If you're seeing "Policy not found" error, follow these steps:

### Step 1: Verify Database Has Policies
```bash
cd backend
.\venv\Scripts\Activate.ps1
python seed_data.py
```

### Step 2: Check Backend is Running
The backend should be running on http://localhost:8000

### Step 3: Test Policy Verification
Try these policy numbers:
- `POL-2024-001`
- `POL-2024-002`
- `POL-2024-003`

## Common Issues

### Issue 1: Backend Not Running
**Solution**: Start the backend server
```bash
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

### Issue 2: Database Not Seeded
**Solution**: Run the seed script
```bash
cd backend
.\venv\Scripts\Activate.ps1
python seed_data.py
```

### Issue 3: Database File Missing
**Solution**: The database will be created automatically when you run the backend

### Issue 4: Policy Expired
**Solution**: Policies expire based on their expiry_date. Check seed_data.py to see expiry dates.

## Verify Everything Works

1. **Check Backend**: http://localhost:8000 should return `{"message":"Health Insurance Claim Portal API"}`

2. **Check API Docs**: http://localhost:8000/docs should show Swagger UI

3. **Test Policy Verification**:
   - Go to http://localhost:3000
   - Enter: `POL-2024-001`
   - Click "Verify Policy"

## Still Having Issues?

1. Make sure both servers are running:
   - Backend: Port 8000
   - Frontend: Port 3000

2. Check the backend terminal for error messages

3. Verify the database file exists: `backend/insurance_claims.db`

4. Try restarting both servers


