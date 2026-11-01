"""Szöveg-előkészítés: normalizálás és mondatokra bontás."""

import re

from bemondo.normaliser.normaliser import normalize

PREFIX = "... "  # a magyar modell ezzel a kezdéssel tanult, a normaliser teszi elé


def normalize_text(text: str, prefix: bool = True) -> str:
    # Rövidítések pontja a kiírt alak után már nem kell (kb. → körülbelül, nem körülbelül.)
    text = re.sub(rf"\b({'|'.join(ABBREVIATIONS)})\.", r"\1", text, flags=re.IGNORECASE)
    out = normalize(text)
    if not prefix and out.startswith(PREFIX):
        out = out[len(PREFIX):]
    return out


def split_sentences(text: str) -> list[str]:
    """Mondatokra bont a nyers szövegen (a normalizálás előtt, hogy a pontok még megvannak).

    A sorszámok pontja (pl. "3. helyezett") nem mondathatár: utána kisbetű vagy szám jön.
    """
    text = re.sub(r"\s+", " ", text.strip())
    # Rövidítések pontja nem mondathatár: Dr. Kovács, kb. 100, stb.
    text = re.sub(rf"\b({'|'.join(ABBREVIATIONS)})\.", lambda m: m.group(1) + DOT, text, flags=re.IGNORECASE)
    parts = re.split(r"(?<=[.!?…])\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ\"„])", text)
    return [p.replace(DOT, ".").strip() for p in parts if p.strip()]


DOT = "\u0001"  # ideiglenes jel a rövidítések pontja helyett


ABBREVIATIONS = ["dr", "kb", "pl", "stb", "ill", "ifj", "id", "özv", "u", "tel", "kft", "zrt", "bt", "ún", "máj", "jan", "febr", "márc", "ápr", "jún", "júl", "aug", "szept", "okt", "nov", "dec"]


def compare_key(text: str) -> str:
    """Összehasonlításhoz: csak betűk és szóközök, kisbetűvel."""
    text = normalize_text(text, prefix=False)
    text = re.sub(r"[^\wáéíóöőúüű ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()
