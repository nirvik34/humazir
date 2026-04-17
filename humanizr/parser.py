

from pathlib import Path

SUPPORTED = {".txt", ".pdf", ".docx", ".md"}


def parse(file_path: str) -> str:
    p = Path(file_path)

    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = p.suffix.lower()

    if suffix not in SUPPORTED:
        raise ValueError(
            f"Unsupported file type: {suffix}\n"
            f"Supported: {', '.join(sorted(SUPPORTED))}"
        )

    if suffix in [".txt", ".md"]:
        return _parse_txt(p)

    elif suffix == ".pdf":
        return _parse_pdf(p)

    elif suffix == ".docx":
        return _parse_docx(p)

    return ""


def _parse_txt(p: Path) -> str:
    return p.read_text(
        encoding="utf-8",
        errors="replace"
    ).strip()


def _parse_pdf(p: Path) -> str:
    try:
        import fitz  
    except ImportError:
        raise ImportError(
            "PyMuPDF required.\nRun: pip install PyMuPDF"
        )

    doc = fitz.open(str(p))

    pages = []

    for page in doc:
        pages.append(page.get_text())

    doc.close()

    return "\n\n".join(pages).strip()


def _parse_docx(p: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docx required.\nRun: pip install python-docx"
        )

    doc = Document(str(p))

    paragraphs = []

    for para in doc.paragraphs:
        text = para.text.strip()

        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs).strip()