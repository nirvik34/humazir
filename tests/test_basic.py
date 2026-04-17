
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from humanizr.detector import detect
from humanizr.skills import _parse_skill
from humanizr.utils import sentences, paragraphs, score_color, score_label


# ── Detector tests ──────────────────────────────────────────────────────────

AI_SAMPLE = """
In today's rapidly evolving technological landscape, these groundbreaking tools stand as a
testament to the transformative potential of artificial intelligence. This pivotal development
underscores the vital role that machine learning plays in shaping the future of software
engineering, fostering innovation and contributing to a broader shift. Furthermore, industry
observers have noted that adoption has accelerated significantly. In conclusion, the future
looks bright, with exciting times ahead.
"""

HUMAN_SAMPLE = """
I've been using these tools for about six months. They help with boilerplate — config files,
test scaffolding. They don't help much with architecture or debugging tricky edge cases.
I've accepted suggestions that compiled fine and still did the wrong thing. The key is
reviewing everything, which takes time. Whether that time is less than writing from scratch
depends entirely on the task.
"""


def test_detect_ai_scores_high():
    result = detect(AI_SAMPLE)
    assert result.ai_score >= 50, f"Expected AI score >= 50, got {result.ai_score}"


def test_detect_human_scores_low():
    result = detect(HUMAN_SAMPLE)
    assert result.ai_score <= 60, f"Expected human score <= 60, got {result.ai_score}"


def test_ai_score_higher_than_human():
    ai_result = detect(AI_SAMPLE)
    human_result = detect(HUMAN_SAMPLE)
    assert ai_result.ai_score > human_result.ai_score, (
        f"AI score {ai_result.ai_score} should be > human score {human_result.ai_score}"
    )


def test_detect_returns_flagged_passages():
    result = detect(AI_SAMPLE)
    assert isinstance(result.flagged_passages, list)


def test_detect_confidence_values():
    result = detect(AI_SAMPLE)
    assert result.confidence in ("low", "medium", "high")


def test_detect_empty_text():
    result = detect("")
    assert result.ai_score == 0


def test_detect_sensitivity_high_raises_score():
    r_med  = detect(AI_SAMPLE, sensitivity="medium")
    r_high = detect(AI_SAMPLE, sensitivity="high")
    assert r_high.ai_score >= r_med.ai_score


def test_detect_sensitivity_low_lowers_score():
    r_med = detect(AI_SAMPLE, sensitivity="medium")
    r_low = detect(AI_SAMPLE, sensitivity="low")
    assert r_low.ai_score <= r_med.ai_score


# ── Skill parser tests ──────────────────────────────────────────────────────

SKILL_MD = """
# test_skill

[humanize]
Use varied sentence lengths.
Avoid em dashes.

[detect]
Watch for furthermore overuse.
Check sentence uniformity.
"""


def test_skill_parse_humanize():
    parsed = _parse_skill(SKILL_MD)
    assert "Use varied sentence lengths." in parsed["humanize"]
    assert "Avoid em dashes." in parsed["humanize"]


def test_skill_parse_detect():
    parsed = _parse_skill(SKILL_MD)
    assert "Watch for furthermore overuse." in parsed["detect"]


def test_skill_parse_empty():
    parsed = _parse_skill("")
    assert parsed == {"humanize": [], "detect": []}


# ── Utils tests ─────────────────────────────────────────────────────────────

def test_sentences_split():
    text = "Hello world. This is a test. And another one."
    sents = sentences(text)
    assert len(sents) == 3


def test_score_color():
    assert score_color(80) == "red"
    assert score_color(50) == "yellow"
    assert score_color(20) == "green"


def test_score_label():
    assert score_label(75) == "LIKELY AI"
    assert score_label(50) == "MIXED"
    assert score_label(10) == "LIKELY HUMAN"


if __name__ == "__main__":
    # Simple runner without pytest
    tests = [
        test_detect_ai_scores_high,
        test_detect_human_scores_low,
        test_ai_score_higher_than_human,
        test_detect_returns_flagged_passages,
        test_detect_confidence_values,
        test_detect_empty_text,
        test_detect_sensitivity_high_raises_score,
        test_detect_sensitivity_low_lowers_score,
        test_skill_parse_humanize,
        test_skill_parse_detect,
        test_skill_parse_empty,
        test_sentences_split,
        test_score_color,
        test_score_label,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
