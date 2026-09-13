"""Parsing for tabletop dice notation strings such as "3d6+2" or "4d6kh3"."""

import re
from dataclasses import dataclass
from typing import Optional

# count is optional (defaults to 1, as in "d20"). sides is digits or "%"
# for d100. keep-highest/keep-lowest and the trailing modifier are both
# optional. Whitespace is tolerated anywhere a human might type it.
_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<count>\d*)
    d
    (?P<sides>\d+|%)
    \s*
    (?:(?P<keep_mode>k[hl])(?P<keep_count>\d+))?
    \s*
    (?P<modifier>[+-]\s*\d+)?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


class ParseError(ValueError):
    """Raised when a string is not valid dice notation."""


@dataclass(frozen=True)
class Keep:
    """Which subset of rolled dice to keep, e.g. "highest 3 of 4"."""

    mode: str  # "highest" or "lowest"
    count: int


@dataclass(frozen=True)
class Roll:
    """A parsed dice expression, ready to be rolled."""

    count: int
    sides: int
    modifier: int = 0
    keep: Optional[Keep] = None


def parse(text: str) -> Roll:
    """Parse dice notation into a Roll.

    Examples: "d20", "3d6", "3d6+2", "4d6kh3" (roll 4d6, keep the
    highest 3), "d%" (percentile die, equivalent to d100).
    """
    match = _PATTERN.match(text)
    if not match:
        raise ParseError(f"invalid dice notation: {text!r}")

    count = int(match["count"]) if match["count"] else 1
    if count < 1:
        raise ParseError("dice count must be at least 1")

    sides = 100 if match["sides"] == "%" else int(match["sides"])
    if sides < 1:
        raise ParseError("a die must have at least 1 side")

    keep = None
    if match["keep_mode"]:
        keep_count = int(match["keep_count"])
        if keep_count < 1:
            raise ParseError("keep count must be at least 1")
        if keep_count > count:
            raise ParseError(f"cannot keep {keep_count} dice out of {count} rolled")
        mode = "highest" if match["keep_mode"][1].lower() == "h" else "lowest"
        keep = Keep(mode, keep_count)

    modifier_text = match["modifier"]
    modifier = int(modifier_text.replace(" ", "")) if modifier_text else 0

    return Roll(count=count, sides=sides, modifier=modifier, keep=keep)
