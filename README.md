# HireLens - AI Resume Screening MVP

HireLens is a college innovation project that ranks resumes against a job description using transparent local NLP. It addresses the problem that recruiters spend significant time screening large numbers of resumes and may struggle to identify strong job-relevant matches.

## Must-have features

- Upload multiple PDF and DOCX resumes at once
- Paste or upload a PDF/DOCX job description
- Extract skills from resumes and the job description
- Score and rank candidates
- Display matched skills in green and missing skills in red
- Download the ranked candidate list as Excel

## Additional features

- Score breakdown: skill score versus TF-IDF text similarity
- Name/file, email, and phone extraction where available
- Minimum-score filter
- Delete-all-data control for the current session
- Five built-in demo candidates so the app works without resume files
- Clear message for empty or scanned-image PDFs

## Project structure

```text
hirelens/
  app.py
  parser.py
  skills.py
  match.py
  data/skills.txt
  requirements.txt
  samples/
```

The previous FastAPI experiment remains in `backend/`, but this Streamlit app is the implementation matching the current specification.

## Installation on Windows PowerShell

```powershell
cd "C:\Users\aarvi\OneDrive\Desktop\College\3rd sem subjects\IP3"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
```

Open the URL shown by Streamlit, usually http://localhost:8501.

## Scoring

```text
skill_score = matched JD skills / total JD skills
text_score = TF-IDF cosine similarity between JD and resume text
final_score = 0.7 * skill_score + 0.3 * text_score
```

Skills are matched with spaCy `PhraseMatcher`, aliases include `ml -> machine learning`, `js -> javascript`, `dl -> deep learning`, and `py -> python`. The fallback matcher also works if the spaCy model is unavailable.

The scoring method is transparent but not scientifically validated. Do not use the score as the sole basis for hiring decisions. The tool should focus only on job-relevant qualifications and must not use gender, age, religion, caste, race, photographs, marital status, or similar irrelevant characteristics.

## Testing ideas

Try Python developer, data analyst, and HR job descriptions. Test a multi-page PDF, a DOCX, a scanned-image PDF, an empty file, and an unsupported file type. For a project report, compare the tool's top five with a human shortlist and record the agreement percentage.
