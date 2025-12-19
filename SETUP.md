# Quick Setup Guide

## Backend (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Backend runs on: http://localhost:8000

## Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## Verify Setup

1. Backend API: Visit http://localhost:8000/api/companies/ - should return JSON list of companies
2. Frontend: Visit http://localhost:5173 - should show the dashboard
3. Click on a node (company) in the network graph to see details
4. Click on an edge to see relationship details

## Troubleshooting

- **CORS errors**: Make sure backend is running and CORS is enabled in settings.py
- **No data**: Run `python manage.py seed_demo` again
- **Port conflicts**: Change ports in `vite.config.js` (frontend) or `settings.py` (backend)

