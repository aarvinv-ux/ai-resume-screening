from functools import lru_cache
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@lru_cache(maxsize=1)
def _embedding_model():
    if os.getenv("HIRELENS_ENABLE_EMBEDDINGS", "false").lower() != "true":
        return None
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        return None
    except Exception:
        return None


def _semantic_similarity(job_text: str, resume_text: str) -> tuple[float, str]:
    model = _embedding_model()
    if model is not None:
        try:
            embeddings = model.encode(
                [job_text, resume_text],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return float(embeddings[0] @ embeddings[1]), "AI semantic similarity"
        except Exception:
            pass

    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([job_text, resume_text])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0]), "TF-IDF fallback"
    except ValueError:
        return 0.0, "TF-IDF fallback"


def _tfidf_scores(job_text: str, resume_texts: list[str]) -> list[float]:
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([job_text, *resume_texts])
        return [float(value) for value in cosine_similarity(matrix[0:1], matrix[1:]).ravel()]
    except ValueError:
        return [0.0] * len(resume_texts)


def _skill_scores(resume_skills: list[str], job_skills: list[str]) -> tuple[float, list[str], list[str]]:
    matched = sorted(set(job_skills).intersection(resume_skills))
    missing = sorted(set(job_skills).difference(resume_skills))
    skill_score = len(matched) / len(job_skills) if job_skills else 0.0
    return skill_score, matched, missing


def _result(skill_score: float, text_score: float, similarity_method: str, matched: list[str], missing: list[str]) -> dict:
    final_score = (0.7 * skill_score + 0.3 * text_score) * 100
    return {
        "score": round(final_score, 1),
        "skill_score": round(skill_score * 100, 1),
        "text_score": round(text_score * 100, 1),
        "similarity_method": similarity_method,
        "matched_skills": matched,
        "missing_skills": missing,
    }


def score_resumes(job_text: str, resumes: list[tuple[str, list[str]]], job_skills: list[str], allow_ai: bool | None = None) -> list[dict]:
    """Score a batch, avoiding transformer memory spikes on hosted free tiers."""
    if not resumes:
        return []

    max_ai_resumes = int(os.getenv("HIRELENS_MAX_AI_RESUMES", "75"))
    if allow_ai is None:
        allow_ai = len(resumes) <= max_ai_resumes

    if len(resumes) > 50:
        results = []
        for start in range(0, len(resumes), 50):
            results.extend(score_resumes(job_text, resumes[start:start + 50], job_skills, allow_ai))
        return results

    semantic_scores = []
    method = "AI semantic similarity" if allow_ai else "TF-IDF large-batch mode"
    if allow_ai:
        model = _embedding_model()
    else:
        model = None
        method = "TF-IDF large-batch mode"

    if model is not None:
        try:
            texts = [job_text[:12000]] + [text[:12000] for text, _ in resumes]
            embeddings = model.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            job_embedding = embeddings[0]
            semantic_scores = [float(job_embedding @ embedding) for embedding in embeddings[1:]]
        except Exception:
            semantic_scores = []

    if not semantic_scores:
        semantic_scores = _tfidf_scores(job_text, [text[:12000] for text, _ in resumes])
        method = "TF-IDF fallback" if allow_ai else "TF-IDF large-batch mode"

    results = []
    for (text, resume_skills), text_score in zip(resumes, semantic_scores):
        skill_score, matched, missing = _skill_scores(resume_skills, job_skills)
        results.append(_result(skill_score, text_score, method, matched, missing))
    return results


def score_resume(resume_text: str, job_text: str, resume_skills: list[str], job_skills: list[str]) -> dict:
    skill_score, matched, missing = _skill_scores(resume_skills, job_skills)
    text_score, similarity_method = _semantic_similarity(job_text, resume_text)
    return _result(skill_score, text_score, similarity_method, matched, missing)
