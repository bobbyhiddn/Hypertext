"""One lemma, one card.

Rule (user, 2026-08-28): a word may not enter the set as a derivative of a word
already in it - a different tense, number, or part of speech of the same root
(CHOOSE / CHOSEN) - unless it prints different lemmas. Two cards may never share
a printed Hebrew lemma or a printed Greek lemma.

Deterministic proxies, applied against every existing card record:

* same Hebrew lemma text (niqqud stripped) or same Greek lemma text (accents
  stripped, final sigma normalised)            -> conflict
* same Hebrew root, approximated by the consonantal skeleton of the
  transliteration (bachar / bachir -> b-ch-r)   -> conflict
* same English stem after suffix stripping, plus a table of irregular pairs
  (CHOOSE / CHOSEN, SPEAK / SPOKEN ...)         -> conflict

The check runs in the plan phase after metadata (hard fail) and as
`hypertext lemma-audit --series` over a whole series.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

_HEBREW_MARKS = re.compile(r"[֑-ׇ]")
_VOWELS = set("aeiouyāēīōūâêîôûáéíóúàèìòù")
_SUFFIXES = ("ness", "ment", "tion", "ing", "est", "ers", "ed", "en", "er", "es", "ly", "s")
_IRREGULAR = {
    "CHOOSE": "CHOS", "CHOSEN": "CHOS", "CHOSE": "CHOS",
    "SPEAK": "SPOK", "SPOKE": "SPOK", "SPOKEN": "SPOK", "SPEECH": "SPOK",
    "BUILD": "BUILT", "BUILT": "BUILT",
    "BREAK": "BROK", "BROKE": "BROK", "BROKEN": "BROK",
    "GIVE": "GAV", "GAVE": "GAV", "GIVEN": "GAV", "GIFT": "GAV",
    "KNOW": "KNOWN", "KNEW": "KNOWN", "KNOWN": "KNOWN",
    "SEE": "SEEN", "SAW": "SEEN", "SEEN": "SEEN",
    "FALL": "FALLEN", "FELL": "FALLEN", "FALLEN": "FALLEN",
    "RISE": "RISEN", "ROSE": "RISEN", "RISEN": "RISEN",
    "SCATTER": "SCATTER", "SCATTERED": "SCATTER",
    "KEEP": "KEEP", "KEEPER": "KEEP", "KEPT": "KEEP",
}


def hebrew_key(text: str) -> str:
    """Hebrew lemma text without vowel points or cantillation."""
    return _HEBREW_MARKS.sub("", unicodedata.normalize("NFC", str(text or ""))).strip()


def greek_key(text: str) -> str:
    """Greek lemma text without accents/breathings, lower-case, final sigma normalised."""
    stripped = "".join(ch for ch in unicodedata.normalize("NFD", str(text or "")) if unicodedata.category(ch) != "Mn")
    return stripped.lower().replace("ς", "σ").strip()


def hebrew_root_key(translit: str) -> str:
    """Consonantal skeleton of a Hebrew transliteration (bachar -> bchr, bachir -> bchr)."""
    t = unicodedata.normalize("NFD", str(translit or "")).lower()
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = re.sub(r"[^a-z]", "", t)
    t = t.replace("sh", "S").replace("ch", "C").replace("ts", "T").replace("kh", "K").replace("th", "H").replace("ph", "F")
    return "".join(ch for ch in t if ch.lower() not in _VOWELS)


def english_stem(word: str) -> str:
    w = re.sub(r"[^A-Z]", "", str(word or "").upper())
    if w in _IRREGULAR:
        return _IRREGULAR[w]
    for suffix in _SUFFIXES:
        # agent/comparative suffixes need a longer remainder (GATHER is not GATH + ER)
        floor = 5 if suffix in ("er", "ers", "est") else 4
        if w.endswith(suffix.upper()) and len(w) - len(suffix) >= floor:
            w = w[: -len(suffix)]
            break
    return w


def _record_keys(content: dict[str, Any]) -> dict[str, str]:
    return {
        "word": str(content.get("WORD", "")).upper(),
        "hebrew": hebrew_key(content.get("HEBREW", "")),
        "greek": greek_key(content.get("GREEK", "")),
        "root": hebrew_root_key(content.get("HEBREW_TRANSLIT", "")),
        "stem": english_stem(content.get("WORD", "")),
    }


def lemma_conflicts(candidate: dict[str, Any], existing: Iterable[tuple[str, dict[str, Any]]]) -> list[dict[str, str]]:
    """Conflicts between a candidate content record and existing (label, content) records."""
    cand = _record_keys(candidate)
    found: list[dict[str, str]] = []
    for label, content in existing:
        other = _record_keys(content)
        if other["word"] == cand["word"]:
            continue
        # A proper name spelled like a common noun (SHEM / NAME) is a homograph,
        # not a derivative: exempt when exactly one of the two is a NAME card.
        homograph = (str(candidate.get("CARD_TYPE", "")).upper() == "NAME") != (str(content.get("CARD_TYPE", "")).upper() == "NAME")
        if cand["hebrew"] and cand["hebrew"] == other["hebrew"] and not homograph:
            found.append({"with": label, "kind": "same-hebrew-lemma", "detail": f"both print {candidate.get('HEBREW')}"})
        if cand["greek"] and cand["greek"] == other["greek"]:
            found.append({"with": label, "kind": "same-greek-lemma", "detail": f"both print {candidate.get('GREEK')}"})
        if len(cand["root"]) >= 3 and cand["root"] == other["root"] and cand["hebrew"] != other["hebrew"] and not homograph:
            found.append({"with": label, "kind": "same-hebrew-root", "detail": f"{candidate.get('HEBREW_TRANSLIT')} / {content.get('HEBREW_TRANSLIT')} share the root {cand['root']}"})
        if len(cand["stem"]) >= 4 and cand["stem"] == other["stem"]:
            found.append({"with": label, "kind": "english-derivative", "detail": f"{cand['word']} and {other['word']} share the stem {cand['stem']}"})
    return found


def load_series_records(series_dir: str | Path, *, skip: str | None = None) -> list[tuple[str, dict[str, Any]]]:
    records: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(Path(series_dir).glob("cards/*/card.json")):
        label = path.parent.name
        if skip and label == skip:
            continue
        try:
            records.append((label, json.loads(path.read_text(encoding="utf-8"))["content"]))
        except (OSError, ValueError, KeyError):
            continue
    return records


def audit_series(series_dir: str | Path) -> list[dict[str, str]]:
    """Every conflicting pair in a series, each pair reported once."""
    records = load_series_records(series_dir)
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for i, (label, content) in enumerate(records):
        for conflict in lemma_conflicts(content, records[i + 1:]):
            key = tuple(sorted((label, conflict["with"]))) + (conflict["kind"],)
            if key in seen:
                continue
            seen.add(key)
            out.append({"card": label, **conflict})
    return out


def summarize(conflicts: list[dict[str, str]]) -> str:
    return "; ".join(f"{c['kind']} with {c['with']} ({c['detail']})" for c in conflicts)


__all__ = ["lemma_conflicts", "audit_series", "load_series_records", "summarize", "hebrew_key", "greek_key", "hebrew_root_key", "english_stem"]
