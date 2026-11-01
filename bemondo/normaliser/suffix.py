"""Szám + kötőjeles toldalék: 2-es → kettes, 12-kor → tizenkettőkor, 100-an → százan.

A dátumos toldalékokat (15-én, 3-án) nem bántja, azokat a normaliser dátumkezelője intézi.
"""

import re

from num2words import num2words

# Toldalékok, amiknél a tőhang rövidül (kettes, hármas, hetes, huszas, ezres)
ADJ_SUFFIXES = {"es", "as", "os", "ös"}
ADJ_STEMS = {"kettő": "kett", "három": "hárm", "hét": "het", "húsz": "husz", "ezer": "ezr"}
# -an/-en (hányan): ketten, hárman, heten, de: húszan, százan
PEOPLE_STEMS = {"kettő": "kett", "három": "hárm", "hét": "het"}

# Minden más toldalék egyszerűen hozzáragad: tizenkettőkor, tíztől, ötig, háromra
PLAIN_SUFFIXES = {
    "kor", "tól", "től", "ig", "ra", "re", "ban", "ben", "ba", "be", "ból", "ből", "ról", "ről",
    "nak", "nek", "val", "vel", "hoz", "hez", "höz", "ért", "on", "en", "ön", "n", "an", "ként",
    "szor", "szer", "ször", "nál", "nél", "ot", "et", "öt", "at", "t",
}
DATE_SUFFIXES = {"án", "én", "jén", "ikén", "dikán", "dikén", "ike", "je", "i", "ei", "ai"}

# Az -on/-en/-ön/-t kötőhang magánhangzós tő után: tizenötön, de "ötöt"; egyszerű eset: kötőjel nélkül ragasztunk
_pattern = re.compile(r"\b(\d+)-([a-záéíóöőúüű]+)\b")


def _attach(words: str, suffix: str) -> str:
    last = words.split()[-1] if " " in words else words
    head = words[: len(words) - len(last)]
    if suffix in ADJ_SUFFIXES:
        for stem, short in ADJ_STEMS.items():
            if last.endswith(stem):
                last = last[: -len(stem)] + short
                break
        else:
            if last.endswith(("a", "e", "o", "ö")):  # kettő már kezelt; pl. "tíz" marad
                pass
    elif suffix in {"an", "en"}:
        for stem, short in PEOPLE_STEMS.items():
            if last.endswith(stem):
                last = last[: -len(stem)] + short
                break
    return head + last + suffix


def replace_number_suffix(text: str) -> str:
    def repl(m):
        num, suffix = int(m.group(1)), m.group(2)
        if suffix in DATE_SUFFIXES:
            return m.group(0)
        if suffix not in ADJ_SUFFIXES and suffix not in PLAIN_SUFFIXES:
            return m.group(0)
        return _attach(num2words(num, lang="hu"), suffix)

    return _pattern.sub(repl, text)
