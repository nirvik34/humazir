

import os
import yaml
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_FILE = _ROOT / "config.yaml"


def load() -> dict:
    """Load config.yaml and merge environment overrides."""
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}
    cfg.setdefault("ai", {})

    cfg["ai"]["provider"] = os.environ.get(
        "HUMANIZR_PROVIDER",
        cfg["ai"].get("provider", "ollama")
    )

    cfg["ai"]["url"] = os.environ.get(
        "OLLAMA_URL",
        cfg["ai"].get("url", "http://127.0.0.1:11434/api/generate")
    )

    cfg["ai"]["model"] = os.environ.get(
        "OLLAMA_MODEL",
        cfg["ai"].get("model", "mistral")
    )

    cfg["ai"]["timeout"] = int(
        os.environ.get(
            "OLLAMA_TIMEOUT",
            cfg["ai"].get("timeout", 120)
        )
    )
    cfg.setdefault("detection", {})
    cfg["detection"].setdefault(
        "default_sensitivity",
        "medium"
    )
    cfg.setdefault("humanizer", {})
    cfg["humanizer"].setdefault(
        "default_style",
        "student"
    )
    cfg.setdefault("output", {})
    cfg["output"].setdefault(
        "reports_dir",
        str(_ROOT / "reports")
    )
    cfg["output"].setdefault(
        "exports_dir",
        str(_ROOT / "exports")
    )
    cfg["output"].setdefault(
        "highlight_marker_open",
        ">> "
    )
    cfg["output"].setdefault(
        "highlight_marker_close",
        " <<"
    )
    cfg.setdefault("skills", {})
    cfg["skills"].setdefault(
        "directory",
        str(_ROOT / "skills")
    )

    return cfg


CFG = load()