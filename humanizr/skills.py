
from pathlib import Path
from humanizr.config import CFG


def _parse_skill(text: str) -> dict:
    result = {
        "humanize": [],
        "detect": []
    }

    current = None

    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.lower() == "[humanize]":
            current = "humanize"
            continue

        elif line.lower() == "[detect]":
            current = "detect"
            continue

        if current:
            result[current].append(line)

    return result


def load_skills(directory=None):
    skills_dir = Path(directory or CFG["skills"]["directory"])

    merged = {
        "humanize": [],
        "detect": []
    }

    if not skills_dir.exists():
        return merged

    for file in sorted(skills_dir.glob("*.md")):
        content = file.read_text(encoding="utf-8", errors="replace")
        parsed = _parse_skill(content)

        merged["humanize"].extend(parsed["humanize"])
        merged["detect"].extend(parsed["detect"])

    return merged


def list_skills(directory=None):
    skills_dir = Path(directory or CFG["skills"]["directory"])

    if not skills_dir.exists():
        return []

    result = []

    for file in sorted(skills_dir.glob("*.md")):
        content = file.read_text(encoding="utf-8", errors="replace")
        parsed = _parse_skill(content)

        result.append({
            "name": file.name,
            "path": str(file),
            "humanize_rules": len(parsed["humanize"]),
            "detect_rules": len(parsed["detect"])
        })

    return result


def add_skill(source_path, directory=None):
    skills_dir = Path(directory or CFG["skills"]["directory"])
    skills_dir.mkdir(parents=True, exist_ok=True)

    src = Path(source_path)

    if not src.exists():
        raise FileNotFoundError(f"Skill file not found: {source_path}")

    dest = skills_dir / src.name
    dest.write_bytes(src.read_bytes())

    return str(dest)


def remove_skill(name, directory=None):
    skills_dir = Path(directory or CFG["skills"]["directory"])

    if not name.endswith(".md"):
        name += ".md"

    target = skills_dir / name

    if target.exists():
        target.unlink()
        return True

    return False