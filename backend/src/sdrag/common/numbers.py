"""Figures in an answer that its cited sources do not contain.

A legal answer is only as good as its periods, ratios and amounts, and the answer model
copies them unchecked: in the v7 answer run it wrote the decree's "1분의 100" (x100) as
"100분의 100" (eval item r0111). This compares figures by value, not by string, because
the answer often says them differently from the source:

- Korean and English: "7일" in a Korean statute is "7 days" in an English answer;
  US statutes write numbers in words ("one thousand eight hundred and forty hours",
  "one and one-half times").
- Fractions and percent: "100분의 25" is 25%, and "1분의 100" is 100 (times).
- Units: 2 weeks is 14 days, 1 year is 12 months.

Only quantities are checked: a number with a unit (days, months, years, hours, weeks,
percent, won, dollars, times, persons, years of age) or a Korean fraction. Article
numbers, list markers and dates are left alone; a year or a day of the month in the
answer is found among the source's numbers anyway (its dates, the version label).

A figure passes if its value, or a unit conversion of it, appears anywhere in the cited
sources (their heading and text). That is lenient on purpose: a check that flags right
answers would teach users to ignore it. It misses a wrong figure that happens to occur
elsewhere in the source; it catches a figure the source does not have at all.
"""

import re

_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}  # fmt: skip
_SCALES = {"hundred": 100, "thousand": 1000, "million": 10**6, "billion": 10**9}
_HALVES = {"one-half": 0.5, "onehalf": 0.5, "half": 0.5, "one-third": 1 / 3, "two-thirds": 2 / 3,
           "one-quarter": 0.25, "one-fourth": 0.25, "three-fourths": 0.75}  # fmt: skip
_WORD = "|".join(sorted([*_ONES, *_SCALES], key=len, reverse=True))
# a run of number words: "two thousand two hundred and forty", "twenty-six", "one and one-half"
RE_WORDS = re.compile(
    rf"\b(?:{_WORD})(?:(?:[\s-]+|\s+and\s+)(?:one-half|onehalf|{_WORD}))*\b",
    re.IGNORECASE,
)
RE_HALF = re.compile(r"\b(?:one-half|onehalf|one-third|two-thirds|one-quarter|one-fourth|three-fourths)\b",
                     re.IGNORECASE)  # fmt: skip
# "100분의 25", "1천분의 2" (1/500), "1분의 100" (x100)
# each scale word may carry digits before it; one way to read any string (no nested
# optional digit runs, which made a long "1천1천1천..." take exponential time), at most 6
_KO_NUM = r"\d[\d,]*(?:\.\d+)?(?:\s*(?:\d[\d,]*\s*)?[천백만억]){0,6}(?:\s*\d[\d,]*)?"
RE_FRACTION = re.compile(rf"({_KO_NUM})\s*분의\s*({_KO_NUM})")
RE_RATIO = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|퍼센트|percent|배|times)", re.IGNORECASE)
RE_DIGITS = re.compile(r"(?<![\d.])\d[\d,]*(?:\.\d+)?")

# the units an answer's figure must carry to be checked, and how to convert them
# a unit that starts a longer word is not a unit: 3주택자, 2회사, 5인증, 10세대, 3건물
_UNITS_KO = (
    r"일|개월|달|년|시간|주(?!택|식|소|민|체|요|관)|분|퍼센트|%|원|배|명(?!의|칭|시|령)|"
    r"인(?!정|가|상|하|증|수|원)|세(?!대|금|액|법)|회(?!사|의|계|원)|건(?!강|물|설|축)"
)
_UNITS_EN = (r"days?|months?|years?|hours?|weeks?|minutes?|percent|per\s?cent|%|won|dollars?|"
             r"times|employees?|workers?|persons?|people|individuals?|members?")  # fmt: skip
# a Korean amount or count: "5천500만원" = 55,000,000, "6억9천만원", "5백명" = 500
RE_KO_AMOUNT = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s*[억천백만](?:\s*(?:\d[\d,]*\s*)?[억천백만]){0,6}(?:\s*\d[\d,]*)?"
    r"(?=\s*(?:원|명|인|개|건|회|세대|가구))"
)
_SCALE = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "천": 1e3, "만": 1e4, "백만": 1e6,
          "천만": 1e7, "억": 1e8}  # fmt: skip
RE_SCALED = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|천만|백만|만|억|천)(?=\s*(?:원|won|달러|dollars?))",
                       re.IGNORECASE)  # fmt: skip
RE_FIGURE = re.compile(
    rf"(?P<cur>\$)?(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>(?:thousand|million|billion)\s+|천만|백만|만|억|천)?\s*"
    rf"(?P<unit>(?:{_UNITS_EN})\b|(?:{_UNITS_KO}))",
    re.IGNORECASE,
)
RE_WORD_FIGURE = re.compile(rf"(?P<num>{RE_WORDS.pattern})[\s-]+(?P<unit>(?:{_UNITS_EN})\b)",
                            re.IGNORECASE)  # fmt: skip
# numbers that are not quantities: article and list references
RE_REFERENCE = re.compile(r"제\s?\d+\s?(?:조|항|호|목|장|절|편)(?:의\s?\d+)?|§+\s?[\d.()a-z-]+|"
                          r"\b(?:Article|Section|Sec\.|Part|Paragraph)s?\s+[\d.()a-z-]+",
                          re.IGNORECASE)  # fmt: skip
# list markers: "1." at a line start, "(3)", circled numbers are not digits anyway
# dates: which version of a statute is in force is decided in code (agent/answer.py)
RE_DATE = re.compile(r"\d{4}\s*년(?:\s*\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?)?|\d{1,2}\s*월\s*\d{1,2}\s*일|"
                     r"\d{4}-\d{2}-\d{2}|\d{4}\.\s?\d{1,2}\.\s?\d{1,2}\.?|"
                     r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}")  # fmt: skip
RE_LIST = re.compile(r"(?m)^\s*\d+\.(?!\d)|\(\d+\)")
_CONVERT = {
    "week": [7],
    "year": [12, 365],
    "month": [1 / 12, 30],
    "day": [24, 1 / 7],
    "hour": [1 / 24],
}
_UNIT_KIND = {
    "일": "day",
    "개월": "month",
    "달": "month",
    "년": "year",
    "시간": "hour",
    "주": "week",
}


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _words(s: str) -> float | None:
    """Value of an English number phrase: "two thousand two hundred and forty" -> 2240,
    "one and one-half" -> 1.5."""
    total, cur, frac, seen = 0, 0, 0.0, False
    for tok in re.split(r"[\s-]+|\band\b", s.lower().replace("one-half", "onehalf")):
        if not tok:
            continue
        if tok in ("onehalf", "half"):
            frac = 0.5
        elif tok in _ONES:
            cur += _ONES[tok]
            seen = True
        elif tok in _SCALES:
            cur = max(cur, 1) * _SCALES[tok]
            if _SCALES[tok] >= 1000:
                total, cur = total + cur, 0
            seen = True
    return total + cur + frac if seen else (frac or None)


def korean_amount(s: str) -> float:
    """ "6억9천만" -> 690000000: 억 and 만 close a group, 천 and 백 scale within one."""
    total, group = 0.0, 0.0
    for num, unit in re.findall(r"(\d[\d,]*(?:\.\d+)?)?\s*(억|만|천|백|$)", s.strip()):
        v = _num(num) if num else None
        if unit in ("천", "백"):
            group += (v if v is not None else 1) * (1000 if unit == "천" else 100)
        elif unit in ("만", "억"):
            total += (group + (v or 0) or 1) * (1e4 if unit == "만" else 1e8)
            group = 0.0
        else:
            total += group + (v or 0)
            group = 0.0
    return total


def _kind(unit: str) -> str:
    u = unit.lower().rstrip("s")
    return _UNIT_KIND.get(unit, u if u in _CONVERT else "")


def source_values(text: str) -> tuple[set[float], set[float]]:
    """(every number in a source: digits, number words, fractions as a ratio and as
    percent; the ratios alone: fractions, percents / 100, multipliers)."""
    vals: set[float] = set()
    ratios: set[float] = set()
    text = RE_LIST.sub(" ", RE_REFERENCE.sub(" ", text))
    for m in RE_FRACTION.finditer(text):
        den, num = korean_amount(m.group(1)), korean_amount(m.group(2))
        if den:
            ratios.add(round(num / den, 6))
            vals |= {round(num / den, 6), round(100 * num / den, 6)}
    rest = RE_FRACTION.sub(" ", text)
    for m in RE_DIGITS.finditer(rest):
        vals.add(round(_num(m.group()), 6))
    for m in RE_KO_AMOUNT.finditer(rest):
        vals.add(round(korean_amount(m.group()), 6))
    for m in RE_SCALED.finditer(rest):  # 50만원 -> 500000, 1.5 million won -> 1500000
        vals.add(round(_num(m.group(1)) * _SCALE[m.group(2).lower()], 6))
    for m in RE_RATIO.finditer(rest):
        v = _num(m.group(1))
        ratios.add(
            round(v / 100, 6)
            if m.group(2) != "배" and not m.group(2).lower().startswith("time")
            else round(v, 6)
        )
    for m in RE_WORDS.finditer(text):
        v = _words(m.group())
        if v is not None:
            vals.add(round(v, 6))
    for m in RE_HALF.finditer(text):
        vals.add(round(_HALVES[m.group().lower()], 6))
    return vals, ratios


def figures(text: str) -> list[tuple[str, list[float], bool]]:
    """The quantities in an answer: (as written, the values that would confirm it, whether
    it is a fraction). A fraction is matched against the source's ratios only: its value
    (1 for "100분의 100") would otherwise be found among any source's plain numbers."""
    text = RE_DATE.sub(" ", RE_REFERENCE.sub(" ", re.sub(r"\[\d+\]", " ", text)))
    out = []
    for m in RE_FRACTION.finditer(text):
        den, num = korean_amount(m.group(1)), korean_amount(m.group(2))
        if den:
            out.append((m.group(), [round(num / den, 6)], True))
    rest = RE_FRACTION.sub(" ", text)
    for m in RE_KO_AMOUNT.finditer(rest):
        unit = re.match(r"\s*(원|명|인|개|건|회|세대|가구)", rest[m.end() :])
        raw = m.group().strip() + (unit.group(1) if unit else "")
        out.append((raw, [round(korean_amount(m.group()), 6)], False))
    rest = RE_KO_AMOUNT.sub(" ", rest)
    for m in [*RE_FIGURE.finditer(rest), *RE_WORD_FIGURE.finditer(rest)]:
        raw = m.group("num")
        if raw[0].isalpha() and rest[: m.start()].rstrip()[-1:].isdigit():
            continue  # "million won" of "1.5 million won", read by RE_FIGURE
        v = _words(raw) if raw[0].isalpha() else _num(raw)
        if v is None:
            continue
        unit = re.sub(r"\s", "", m.group("unit"))
        scale = (m.groupdict().get("scale") or "").strip().lower()
        if scale:
            v *= _SCALE[scale]
        elif v == 1 and _kind(unit):
            continue  # "1일 8시간", "1년마다", "per day": a rate, not a period
        if unit.lower() in ("%", "퍼센트") or unit.lower().startswith("per"):
            cands = [v, v / 100]
        else:
            cands = [v] + [v * f for f in _CONVERT.get(_kind(unit), [])]
        out.append((m.group().strip(), [round(c, 6) for c in cands], False))
    return out


def unsupported(answer: str, sources: list[str], question: str = "") -> list[str]:
    """Figures in `answer` that none of `sources` contains, as written in the answer. A
    figure the question itself gives ("보증금 1억5천만원으로 계약했는데") may be repeated."""
    vals: set[float] = set()
    ratios: set[float] = set()
    for s in [*sources, question]:
        v, r = source_values(s)
        vals |= v
        ratios |= r
    seen, out = set(), []
    for raw, cands, fraction in figures(answer):
        ok = any(c in (ratios if fraction else vals) for c in cands)
        if not ok and raw not in seen:
            seen.add(raw)
            out.append(raw)
    return out
