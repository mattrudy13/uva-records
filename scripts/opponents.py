"""Turn the site's free-text opponent names into one name per school.

The site stores whatever was typed: "@ #13 Duke (on WINA)", "DUKE (DH Game 1)",
"Duke - NCAA Final". clean() strips that decoration, key() folds case and
punctuation, and data/aliases.json maps true aliases (UNC, Pitt, VCU) to one school.

Usage: .venv/bin/python scripts/opponents.py   # prints names that still need review
"""

import difflib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALIASES = ROOT / "data" / "aliases.json"

# Parentheticals that are part of a school's name, not a note about the game.
QUALIFIERS = {
    "md", "oh", "ohio", "pa", "ny", "fl", "fla", "calif", "ca", "sc", "nj", "tenn", "tn", "mn",
    "brooklyn", "texas", "tx", "ill", "il", "ind", "in", "ky", "mass", "ma", "la", "va", "nc",
    "wis", "minn", "mich", "ga", "ala", "conn", "me", "vt", "nh", "ri", "de", "wv", "w va",
}
KEEP_SUFFIX = {"boston college", "boston university", "miami university", "college of charleston"}
PREFIX = re.compile(
    r"^\s*(?:@|at\s|vs\.?\s|#\d+(?:/\d+)?\s|\(\d+\)\s|no\.\s*\d+\s+(?:seed\s+)?|\d+-seed\s+|"
    r"ncaa (?:rd|round) of \d+ (?:vs\.?|-)\s*|"
    r"(?:acc|ncaa)\s+(?:championship|tournament|(?:first|second|third) round|quarterfinals?|semifinals?|finals?)"
    r"\s*(?:vs\.?\s|-\s)?)",
    re.I,
)
PAREN = re.compile(r"\s*\(([^()]*)\)")
DASH_NOTE = re.compile(r"\s+-\s+.*$")
AT_VIRGINIA = re.compile(r"\s+(@\s+virginia|virginia duals|@)$", re.I)


def clean(name):
    s = (name or "").strip()
    while True:
        t = PREFIX.sub("", s, count=1).strip()
        if t == s:
            break
        s = t
    s = AT_VIRGINIA.sub("", DASH_NOTE.sub("", s))

    def keep(m):
        inner = re.sub(r"[^a-z ]", "", m.group(1).lower()).strip()
        return f" ({m.group(1).strip()})" if inner in QUALIFIERS else ""

    s = PAREN.sub(keep, s).strip()
    if s.isupper() and len(s) > 4:  # "SETON HALL" -> "Seton Hall"; leaves "UMBC", "VCU"
        s = s.title()
    return s


def key(name):
    """Comparison key: lowercase, no punctuation, St./Saint folded, trailing St -> State."""
    s = re.sub(r"[^a-z0-9 ]+", " ", name.lower().replace("&", " and ")).strip()
    # "Duke University" and "Duke" are one school, but "Boston College" and "Boston
    # University" aren't, so these words only drop when the rest isn't ambiguous.
    if s not in KEEP_SUFFIX:
        s = re.sub(r"^(the )?university of |^the | (university|college)$", " ", s).strip()
    words = s.split()
    words = ["saint" if w == "st" and i == 0 else w for i, w in enumerate(words)]
    if len(words) > 1 and words[-1] == "st":
        words[-1] = "state"
    return " ".join(words)


def load_aliases():
    raw = json.loads(ALIASES.read_text()) if ALIASES.exists() else {}
    return {key(k): v for k, v in raw.items()}


def canonical(name, aliases=None):
    """The display name for an opponent, or "" if the game has no single opponent."""
    aliases = load_aliases() if aliases is None else aliases
    c = clean(name)
    return aliases.get(key(c), c)


def main():
    aliases = load_aliases()
    counts = Counter()
    for path in sorted((ROOT / "data" / "games").glob("*.json")):
        for g in json.loads(path.read_text()):
            if g["kind"] == "official":
                counts[canonical(g["school"], aliases)] += 1
    # Different display names that share a key are spelling variants; pick one.
    by_key = {}
    for name in counts:
        by_key.setdefault(key(name), []).append(name)
    print(f"{len(counts)} opponent names")
    for k, names in sorted(by_key.items()):
        if len(names) > 1:
            print("same key:", names)
    keys = sorted(by_key)
    for k in keys:
        near = [n for n in difflib.get_close_matches(k, keys, n=3, cutoff=0.86) if n != k]
        if near and k < near[0]:
            print("similar:", by_key[k], [by_key[n] for n in near])


if __name__ == "__main__":
    main()
