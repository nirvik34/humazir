
import re
import math
from dataclasses import dataclass, field
from humanizr.utils import sentences, paragraphs, truncate


# ── Signals ────────────────────────────────────────────────────────────────

AI_VOCAB = [
    "groundbreaking", "pivotal", "transformative", "revolutionary", "cutting-edge",
    "comprehensive", "robust", "synergy", "leverage", "paradigm", "seamless",
    "streamline", "utilize", "facilitate", "encompass", "furthermore", "moreover",
    "additionally", "nevertheless", "consequently", "subsequently", "delve",
    "testament", "underscores", "showcases", "highlights", "emphasizes",
    "vibrant", "nestled", "breathtaking", "stunning", "renowned",
    "in today's", "rapidly evolving", "evolving landscape",
    "in conclusion", "it is important to note", "it is worth noting",
    "in order to", "foster", "cultivate",
]

INFLATION_PATTERNS = [
    r"stands? as a (testament|reminder|symbol)",
    r"marks? a (pivotal|crucial|key|significant) moment",
    r"underscores? (the|its|their) (importance|significance|vital role)",
    r"reflects? broader (trends?|shifts?|movements?)",
    r"in today'?s? rapidly evolving",
    r"(fostering|cultivating|showcasing|highlighting|emphasizing)\s+\w+",
    r"(serves?|functions?|stands?) as (a|an|the)\b",
    r"it is (important|crucial|essential|worth) to note",
    r"(furthermore|moreover|additionally|consequently|subsequently)[,.]",
    r"in conclusion[,.]",
    r"the future (looks?|seems?) bright",
    r"exciting times? (lie|lay) ahead",
    r"industry (observers?|experts?) (have|has) noted",
    r"experts? (argue|believe|suggest|claim)",
]

TRANSITION_WORDS = [
    "furthermore", "moreover", "additionally", "consequently",
    "subsequently", "in conclusion", "in summary", "ultimately",
    "nevertheless", "therefore", "thus", "hence",
]


# ── Scoring functions ──────────────────────────────────────────────────────

def _burstiness(sents: list) -> float:
    if len(sents) < 3:
        return 0.5
    lengths = [len(s.split()) for s in sents]
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.5
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    cv = math.sqrt(variance) / mean   # coefficient of variation
    # Low CV = uniform = AI. We return how AI-like (1 = very AI).
    return max(0.0, min(1.0, 1.0 - (cv / 0.6)))


def _transition_density(text: str) -> float:
    words = text.lower().split()
    total_words = max(len(words), 1)
    hits = sum(words.count(t.split()[0]) for t in TRANSITION_WORDS)
    density = (hits / total_words) * 100  # per 100 words
    return min(1.0, density / 3.0)


def _vocab_signal(text: str) -> float:
    lower = text.lower()
    hits = sum(1 for w in AI_VOCAB if w in lower)
    return min(1.0, hits / 6.0)


def _inflation_signal(text: str) -> tuple:
    lower = text.lower()
    matched = []
    for pat in INFLATION_PATTERNS:
        m = re.search(pat, lower)
        if m:
            matched.append(m.group(0))
    return min(1.0, len(matched) / 4.0), matched


def _em_dash_signal(text: str) -> float:
    count = text.count("—") + text.count("–")
    sents = sentences(text)
    if not sents:
        return 0.0
    return min(1.0, count / max(len(sents) / 3, 1))


def _para_uniformity(paras: list) -> float:
    if len(paras) < 2:
        return 0.0
    starters = [p.split()[0].lower() for p in paras if p.split()]
    unique_ratio = len(set(starters)) / len(starters)
    return round(1.0 - unique_ratio, 2)


def _find_flagged(text: str, extra_patterns: list = None) -> list:
    all_patterns = INFLATION_PATTERNS + (extra_patterns or [])
    sents = sentences(text)
    flagged = []
    for i, sent in enumerate(sents):
        sl = sent.lower()
        flags = []
        for w in AI_VOCAB[:14]:
            if w in sl:
                flags.append(f'ai vocab "{w}"')
        for pat in all_patterns[:8]:
            if re.search(pat, sl):
                flags.append("inflation phrase")
                break
        if "—" in sent or "–" in sent:
            flags.append("em dash")
        if flags:
            flagged.append({
                "line": i + 1,
                "excerpt": truncate(sent, 100),
                "flags": list(set(flags)),
            })
    return flagged


# ── Main entry point ───────────────────────────────────────────────────────

@dataclass
class DetectionResult:
    ai_score: int
    confidence: str
    verdict: str
    flagged_passages: list = field(default_factory=list)
    signals: dict = field(default_factory=dict)
    human_signals: list = field(default_factory=list)


def detect(
    text: str,
    sensitivity: str = "medium",
    extra_detect_rules: list = None,
) -> DetectionResult:
    text = text.strip()
    if not text:
        return DetectionResult(0, "low", "No text provided.")

    sents = sentences(text)
    paras = paragraphs(text)

    bust  = _burstiness(sents)
    trans = _transition_density(text)
    vocab = _vocab_signal(text)
    infl, infl_hits = _inflation_signal(text)
    em    = _em_dash_signal(text)
    para  = _para_uniformity(paras)

    raw = (
        bust  * 0.25 +
        trans * 0.15 +
        vocab * 0.20 +
        infl  * 0.25 +
        em    * 0.05 +
        para  * 0.10
    )

    adj = {"low": -0.08, "medium": 0.0, "high": 0.08}
    raw = max(0.0, min(1.0, raw + adj.get(sensitivity, 0.0)))
    score = int(raw * 100)

    strong = sum([bust > 0.5, trans > 0.4, vocab > 0.4, infl > 0.3])
    confidence = "high" if strong >= 3 else "medium" if strong >= 2 else "low"

    if score >= 70:
        verdict = "Likely AI-generated. Multiple strong signals detected."
    elif score >= 45:
        verdict = "Mixed signals. Possibly AI-assisted or heavily edited."
    elif score >= 25:
        verdict = "Mostly human. A few AI patterns present."
    else:
        verdict = "Likely human-written. Few AI signals found."

    human_signals = []
    if bust < 0.3:
        human_signals.append("varied sentence rhythm")
    if trans < 0.2:
        human_signals.append("natural transitions")
    if vocab < 0.2:
        human_signals.append("no AI vocabulary detected")

    return DetectionResult(
        ai_score=score,
        confidence=confidence,
        verdict=verdict,
        flagged_passages=_find_flagged(text, extra_detect_rules),
        signals={
            "burstiness": round(bust, 2),
            "transitions": round(trans, 2),
            "vocabulary": round(vocab, 2),
            "inflation": round(infl, 2),
            "em_dash": round(em, 2),
            "para_uniformity": round(para, 2),
        },
        human_signals=human_signals,
    )
