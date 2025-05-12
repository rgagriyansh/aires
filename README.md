# Full Stack Application

This is a full-stack application with a Next.js frontend and FastAPI backend.

## Project Structure

```
.
├── backend/           # Python FastAPI backend
│   ├── main.py       # Main FastAPI application
│   ├── requirements.txt
│   └── README.md
└── frontend/         # Next.js frontend
    ├── pages/
    │   └── index.tsx
    ├── package.json
    └── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the frontend development server:
```bash
npm run dev
```

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend API Documentation: http://localhost:8000/docs 