from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def score_resume(resume_text: str, job_text: str, resume_skills: list[str], job_skills: list[str]) -> dict:
    matched = sorted(set(job_skills).intersection(resume_skills))
    missing = sorted(set(job_skills).difference(resume_skills))
    skill_score = len(matched) / len(job_skills) if job_skills else 0.0
    documents = [job_text, resume_text]
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform(documents)
        text_score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        text_score = 0.0
    final_score = (0.7 * skill_score + 0.3 * text_score) * 100
    return {"score": round(final_score, 1), "skill_score": round(skill_score * 100, 1), "text_score": round(text_score * 100, 1), "matched_skills": matched, "missing_skills": missing}
