
import re
from pathlib import Path


def sentences(text: str) -> list:
    return [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', text)
        if len(s.strip()) > 10
    ]


def paragraphs(text: str) -> list:
    return [
        p.strip()
        for p in re.split(r'\n{2,}', text)
        if len(p.strip()) > 30
    ]


def word_count(text: str) -> int:
    return len(text.split())


def truncate(text: str, n: int = 90) -> str:
    if len(text) > n:
        return text[:n] + "..."
    return text


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def score_color(score: int) -> str:
    if score >= 70:
        return "red"
    elif score >= 45:
        return "yellow"
    return "green"


def score_label(score: int) -> str:
    if score >= 70:
        return "LIKELY AI"
    elif score >= 45:
        return "MIXED"
    return "LIKELY HUMAN"