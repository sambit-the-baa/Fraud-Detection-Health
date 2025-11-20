# GitHub Setup Instructions

## Quick Setup

### Option 1: If repository doesn't exist on GitHub

1. **Create repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `Fraud-detection`
   - Description: "Health Insurance Claim Portal with AI-powered fraud detection"
   - Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license
   - Click "Create repository"

2. **Push your code:**
   ```bash
   cd "C:\Fraud detection"
   git remote add origin https://github.com/YOUR_USERNAME/Fraud-detection.git
   git branch -M main
   git push -u origin main
   ```

### Option 2: If repository already exists

1. **Set the remote URL:**
   ```bash
   cd "C:\Fraud detection"
   git remote set-url origin https://github.com/YOUR_USERNAME/Fraud-detection.git
   git branch -M main
   git push -u origin main
   ```

## Replace YOUR_USERNAME

Replace `YOUR_USERNAME` with your actual GitHub username in the commands above.

## What's Included

The repository includes:
- ✅ Complete backend (FastAPI)
- ✅ Complete frontend (React)
- ✅ Database models and migrations
- ✅ AI fraud detection service
- ✅ All improvements and security fixes
- ✅ Documentation (README, setup guides)
- ✅ .gitignore (excludes sensitive files, node_modules, venv, etc.)

## Files Excluded (.gitignore)

- `backend/venv/` - Python virtual environment
- `backend/.env` - Environment variables (sensitive)
- `backend/uploads/` - Uploaded documents
- `backend/*.db` - Database files
- `frontend/node_modules/` - Node dependencies
- `__pycache__/` - Python cache files

## After Pushing

1. Add a `.env.example` file to show required environment variables
2. Update README with deployment instructions
3. Add GitHub Actions for CI/CD (optional)
4. Add issues/PR templates (optional)

## Troubleshooting

### Authentication Issues
If you get authentication errors:
- Use GitHub Personal Access Token instead of password
- Or use SSH: `git@github.com:YOUR_USERNAME/Fraud-detection.git`

### Large Files
If uploads are too large:
- They're already in .gitignore
- Use Git LFS for large files if needed

