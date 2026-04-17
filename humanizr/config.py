import os
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.yaml"
USER_CONFIG_FILE = Path.home() / ".humanizr.json"



def load_config() -> dict:
    """Load per-user saved settings."""
    if USER_CONFIG_FILE.exists():
        try:
            import json
            return json.loads(USER_CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_config(data: dict):
    """Save per-user settings."""
    import json
    USER_CONFIG_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


def load() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    user_cfg = load_config()

    cfg.setdefault("ai", {})

    cfg["ai"]["provider"] = os.environ.get(
        "HUMANIZR_PROVIDER",
        cfg["ai"].get("provider", "ollama")
    )

    cfg["ai"]["url"] = os.environ.get(
        "OLLAMA_URL",
        cfg["ai"].get(
            "url",
            "http://127.0.0.1:11434/api/generate"
        )
    )

    cfg["ai"]["model"] = os.environ.get(
        "OLLAMA_MODEL",
        user_cfg.get(
            "model",
            cfg["ai"].get("model", "mistral")
        )
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
        str(ROOT / "reports")
    )

    cfg["output"].setdefault(
        "exports_dir",
        str(ROOT / "exports")
    )

    cfg["output"].setdefault(
        "highlight_marker_open",
        ">> "
    )

    cfg["output"].setdefault(
        "highlight_marker_close",
        " <<"
    )

    # ---------------- Skills ----------------

    cfg.setdefault("skills", {})
    cfg["skills"].setdefault(
        "directory",
        str(ROOT / "skills")
    )

    return cfg


CFG = load()