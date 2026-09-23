# AI Resume Screening System - Python MVP

## Run
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000.

The app seeds five demo candidates on first run. Upload PDF or DOCX files from the dashboard. Data is stored in `data/screening.db`; uploaded files remain local in `uploads/`.

## API
- `GET /api/health`
- `GET /api/job`
- `POST /api/job`
- `GET /api/candidates`
- `POST /api/upload`
- `DELETE /api/candidates/{id}`

Scoring uses required skills 40%, preferred skills 15%, relevant experience 20%, projects 15%, and education/certifications 10%. These weights are transparent design choices, not scientifically validated. The recommendation must not be used as the sole basis for hiring decisions.
