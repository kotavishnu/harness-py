import re
from typing import Callable

ScorerFn = Callable[[str, str], float]

NUMBER_WORDS: dict[str, str] = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12",
}

_WORD_PATTERN = re.compile(
    r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b"
)


def normalize(text: str) -> str:
    return _WORD_PATTERN.sub(
        lambda m: NUMBER_WORDS[m.group(0)],
        text.strip().lower(),
    )


def score_exact_match(actual: str, expected: str) -> float:
    return 1.0 if normalize(actual) == normalize(expected) else 0.0


def score_contains(actual: str, expected: str) -> float:
    return 1.0 if normalize(expected) in normalize(actual) else 0.0


def score_keywords(actual: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    text = normalize(actual)
    hits = sum(1 for k in keywords if normalize(k) in text)
    return hits / len(keywords)
