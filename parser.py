from pathlib import Path
import io
import re
from html.parser import HTMLParser

import pdfplumber
import requests
from docx import Document


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _read_pdf_bytes(content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        text = " ".join(page.extract_text() or "" for page in pdf.pages)
    return _normalize_text(text)


def _read_docx_bytes(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    text = " ".join(paragraph.text for paragraph in document.paragraphs)
    return _normalize_text(text)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data and data.strip():
            self.parts.append(data.strip())

    def get_text(self):
        return _normalize_text(" ".join(self.parts))


def read_resume(uploaded_file) -> str:
    """Read a PDF or DOCX upload into normalized plain text."""
    name = uploaded_file.name.lower()
    content = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        return _read_pdf_bytes(content)
    if name.endswith(".docx"):
        return _read_docx_bytes(content)
    raise ValueError("Only PDF and DOCX files are supported.")


def read_resume_from_url(url: str) -> str:
    """Read a resume from a public URL or a resume page."""
    url = url.strip()
    if not url:
        raise ValueError("Resume URL is empty.")
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    lower_url = url.lower()
    if "application/pdf" in content_type or lower_url.endswith(".pdf"):
        return _read_pdf_bytes(response.content)
    if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type or lower_url.endswith(".docx"):
        return _read_docx_bytes(response.content)

    parser = _HTMLTextExtractor()
    parser.feed(response.text)
    text = parser.get_text()
    if text:
        return text
    return _normalize_text(response.text)


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
