# CV ATS Checker Backend

A Python-based backend for analyzing CVs (PDFs) for Applicant Tracking System (ATS) friendliness.

## Features
- **ATS Scoring**: Calculates a score (0-100) based on content, layout, and extractability.
- **Section Detection**: Checks for "Experience", "Education", "Skills" (and variations like "Employment History", "Professional Skills").
- **Contact Info**: Detects Email and Phone numbers.
- **Early Career Logic**: Adapts requirements for Interns, Trainees, and Students.
- **Layout Analysis**: Detects multi-column layouts and images.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/OneZ-9/cv-ats-checker.git
cd cv-ats-checker
```

### 2. Create a Virtual Environment
It's recommended to use a virtual environment to manage dependencies.

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Run the Server
```bash
uvicorn backend.main:app --reload --port 8001
```
The server will start at `http://127.0.0.1:8001`.

### 5. API Usage
**Endpoint:** `POST /analyze`

**Example using cURL:**
```bash
curl -X POST -F "file=@/path/to/your/cv.pdf" http://127.0.0.1:8001/analyze
```

**Response Example:**
```json
{
  "filename": "cv.pdf",
  "ats_friendly_score": 85,
  "status": "ATS Optimized",
  "missing_sections": [],
  "recommendations": []
}
```

## Running Tests
To verify the logic, run the test script:
```bash
python backend/test_api.py
```
