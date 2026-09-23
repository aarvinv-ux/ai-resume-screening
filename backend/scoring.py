import re

WEIGHTS = {"required": 40, "preferred": 15, "experience": 20, "projects": 15, "education": 10}

def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", " ", value.lower())

def contains(text: str, skill: str) -> bool:
    return norm(skill) in norm(text)

def analyze(profile: dict, job: dict) -> dict:
    searchable = " ".join([
        profile.get("summary", ""), " ".join(profile.get("skills", [])),
        " ".join(profile.get("projects", [])), profile.get("experience_summary", ""),
        profile.get("education", ""), " ".join(profile.get("certifications", []))
    ])
    required = [s for s in job["required_skills"] if contains(searchable, s)]
    preferred = [s for s in job["preferred_skills"] if contains(searchable, s)]
    missing = [s for s in job["required_skills"] + job["preferred_skills"] if s not in required + preferred]
    required_pct = round(len(required) / max(len(job["required_skills"]), 1) * 100)
    preferred_pct = round(len(preferred) / max(len(job["preferred_skills"]), 1) * 100)
    experience_pct = min(100, round(float(profile.get("experience_years", 0)) / 2 * 100))
    projects_pct = min(100, len(profile.get("projects", [])) * 35)
    education_pct = 80 if profile.get("education") else 20
    score = round(required_pct * .40 + preferred_pct * .15 + experience_pct * .20 + projects_pct * .15 + education_pct * .10)
    return {**profile, "matched_skills": required + preferred, "missing_skills": missing,
            "skills_match": required_pct, "score": score,
            "status": "Shortlisted" if score >= 72 else "Needs review",
            "breakdown": {"required": required_pct, "preferred": preferred_pct,
                          "experience": experience_pct, "projects": projects_pct, "education": education_pct},
            "explanation": f"Matched {len(required)} of {len(job['required_skills'])} required skills and {len(preferred)} preferred skills, with {profile.get('experience_years', 0)} years of relevant experience."}
