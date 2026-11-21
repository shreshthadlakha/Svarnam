"""A7 advice-language gate (PRD A7).

Scans the VISIBLE copy of site/*.html (tags stripped) for blocklisted
advice-shaped language. Negated compliance phrases in the fixed disclaimer
("no forecasts", "no price targets", "no recommendation …") are removed
before scanning — they are the guardrail, not a violation. assets/vendor/
is excluded entirely (third-party minified JS). Exit 1 on any hit.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"

BLOCKLIST = [
    r"\btarget(?:s|ed|ing)?\b",
    r"\bforecast(?:s|ed|ing)?\b",
    r"\bwill reach\b",
    r"\bshould buy\b",
    r"\bshould sell\b",
    r"\bexpect(?:ed|s)?\b",
    r"\bguaranteed\b",
    r"\binvest now\b",
    r"\bprice prediction\b",
    r"\bbuy now\b",
    r"\bsell now\b",
]

NEGATIONS = [
    r"no\s+forecasts?",
    r"no\s+price\s+targets?",
    r"no\s+recommendation\s+to\s+buy,?\s+sell,?\s+or\s+avoid\s+anything",
    r"contains\s+no\s+forecasts?",
    r"does\s+not\s+predict\s+prices?",
    r"we\s+show\s+none",
    r"computes\s+no\s+fair\s+value",
    r"makes\s+no\s+valuation\s+claim",
    r"no\s+opinions",
    r"we\s+do\s+not\s+advise",
    r"we\s+compare,\s+we\s+do\s+not\s+advise",
]


def strip_html(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def scan() -> list[str]:
    hits = []
    for f in sorted(SITE.rglob("*.html")):
        if "vendor" in f.parts:
            continue
        text = strip_html(f.read_text(encoding="utf-8"))
        for neg in NEGATIONS:
            text = re.sub(neg, " [compliance-negation] ", text, flags=re.I)
        for pat in BLOCKLIST:
            for m in re.finditer(pat, text, flags=re.I):
                ctx = text[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                hits.append(f"{f.relative_to(SITE)}: /{pat}/ …{ctx}…")
    return hits


def main() -> int:
    hits = scan()
    if hits:
        print("A7 GATE FAILED — advice-shaped language found in site copy:")
        for h in hits:
            print("  !", h)
        return 1
    print("A7 gate: PASS — no advice-shaped language in site copy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
