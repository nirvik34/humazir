import os
import requests
from dataclasses import dataclass, field
from humanizr.config import load_config

import json

CONFIG_PATH = os.path.expanduser("~/.humanizr.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
config = load_config()
MODEL = config.get("model", "deepseek-coder:6.7b")


STYLES = {
    "student": "Write like a smart university student. Natural tone. Slight imperfections.",
    "casual": "Write casually like explaining to a friend.",
    "expert": "Write clearly like a professional expert.",
    "journalist": "Write concise factual journalist style."
}


BASE_SYSTEM = """
Rewrite the text to sound naturally human.

Rules:
- Keep meaning same
- Remove robotic wording
- Vary sentence lengths
- Use contractions naturally
- Remove repeated transitions
- Add human rhythm
- No labels
Return only rewritten text.
"""


@dataclass
class HumanizeResult:
    original: str
    rewritten: str
    style: str
    changes: list = field(default_factory=list)
    word_count_before: int = 0
    word_count_after: int = 0


def _detect_changes(original, rewritten):
    changes = []

    if len(original.split(".")) != len(rewritten.split(".")):
        changes.append("Restructured sentence flow")

    if original != rewritten:
        changes.append("Naturalized tone")

    if not changes:
        changes.append("Minor refinements")

    return changes


def humanize(text: str, style="student", skill_rules=None):

    style_note = STYLES.get(style, STYLES["student"])

    skill_block = ""
    if skill_rules:
        skill_block = "\n".join(skill_rules)

    prompt = f"""
{BASE_SYSTEM}

STYLE:
{style_note}

ADDITIONAL RULES:
{skill_block}

TEXT:
{text}
"""

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        if resp.status_code != 200:
            raise RuntimeError("Ollama request failed")

        rewritten = resp.json()["response"].strip()

    except Exception as e:
        raise RuntimeError(
            "Could not connect to Ollama.\nRun:\nollama serve"
        )

    return HumanizeResult(
        original=text,
        rewritten=rewritten,
        style=style,
        changes=_detect_changes(text, rewritten),
        word_count_before=len(text.split()),
        word_count_after=len(rewritten.split())
    )