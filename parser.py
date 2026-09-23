from pathlib import Path
import io
import re

import pdfplumber
from docx import Document


def read_resume(uploaded_file) -> str:
    """Read a PDF or DOCX upload into normalized plain text."""
    name = uploaded_file.name.lower()
    content = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = " ".join(page.extract_text() or "" for page in pdf.pages)
    elif name.endswith(".docx"):
        document = Document(io.BytesIO(content))
        text = " ".join(paragraph.text for paragraph in document.paragraphs)
    else:
        raise ValueError("Only PDF and DOCX files are supported.")
    return re.sub(r"\s+", " ", text).strip()


def read_job_description(uploaded_file) -> str:
    return read_resume(uploaded_file)


def extract_contact(text: str) -> dict[str, str]:
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    return {"email": email.group(0) if email else "Not found", "phone": phone.group(0) if phone else "Not found"}


def extract_name(text: str, fallback: str = "Unknown candidate") -> str:
    """Use the first plausible heading before falling back to the file name."""
    blocked = {"resume", "curriculum vitae", "cv", "profile", "contact", "summary"}
    for line in text.splitlines():
        candidate = re.sub(r"\s+", " ", line).strip(" -|:")
        words = candidate.split()
        if 2 <= len(words) <= 5 and candidate.lower() not in blocked and not re.search(r"[@\d]", candidate):
            return candidate
    return fallback
