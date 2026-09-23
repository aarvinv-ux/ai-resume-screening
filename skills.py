from pathlib import Path
import re

import spacy
from spacy.matcher import PhraseMatcher

ALIASES = {"ml": "machine learning", "js": "javascript", "dl": "deep learning", "py": "python"}
SKILLS_PATH = Path(__file__).parent / "data" / "skills.txt"

try:
    NLP = spacy.load("en_core_web_sm")
except OSError:
    NLP = spacy.blank("en")

SKILLS = [line.strip().lower() for line in SKILLS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
MATCHER = PhraseMatcher(NLP.vocab, attr="LOWER")
MATCHER.add("SKILL", [NLP.make_doc(skill) for skill in SKILLS])


def expand_aliases(text: str) -> str:
    for alias, value in ALIASES.items():
        text = re.sub(rf"\b{re.escape(alias)}\b", value, text, flags=re.IGNORECASE)
    return text


def extract_skills(text: str) -> list[str]:
    expanded = expand_aliases(text.lower())
    document = NLP(expanded)
    found = {document[start:end].text.lower() for _, start, end in MATCHER(document)}
    if not found:
        found = {skill for skill in SKILLS if re.search(rf"\b{re.escape(skill)}\b", expanded)}
    return sorted(found)
