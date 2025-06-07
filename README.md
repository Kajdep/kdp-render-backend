# KDP Advertising Tool - Render Backend

Flask backend for the KDP Advertising Tool, optimized for Render.com deployment.

## Features

- Complete KDP advertising analysis and optimization
- Supabase authentication and database
- OpenRouter AI integration
- Report processing (CSV/Excel)
- Campaign optimization recommendations
- Export capabilities (CSV, PDF)
- User management and profiles

## Deployment on Render

### Environment Variables Required:
```
SUPABASE_URL=https://zdxllzexzlyaknakzvij.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpkeGxsemV4emx5YWtuYWt6dmlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkyNzAzOTUsImV4cCI6MjA2NDg0NjM5NX0.pYXlejjHZAsrLeLMDZvZLuMys8MjZCAXiG1VECv7Xls
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpkeGxsemV4emx5YWtuYWt6dmlqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTI3MDM5NSwiZXhwIjoyMDY0ODQ2Mzk1fQ.DQri9eqhHE79q6KSoPrbueg4riJSx8s--oqbja7LwWM
SECRET_KEY=kdp-advertising-tool-super-secret-key-2024
FLASK_ENV=production
PORT=10000
```

### Render Configuration:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main_supabase.py`
- **Environment**: Python 3
- **Instance Type**: Free (or upgrade as needed)

## API Endpoints

- `GET /health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/reports/upload` - Upload advertising reports
- `GET /api/analysis/analyze` - Analyze campaign performance
- `GET /api/optimization/optimize` - Get optimization recommendations
- `GET /api/export/csv` - Export data as CSV
- `GET /api/export/pdf` - Export data as PDF

## Local Development

```bash
pip install -r requirements.txt
python main_supabase.py
```

## Production Deployment

This backend is optimized for Render.com with:
- Proper port binding using PORT environment variable
- Production-ready error handling
- CORS enabled for frontend integration
- All dependencies including pandas/numpy (work fine on Render!)
- Gunicorn for production WSGI server

