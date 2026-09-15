"""Parsing for tabletop dice notation strings such as "3d6+2" or "4d6kh3"."""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, Union

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

# One signed term in a multi-group expression such as "3d6+2d4-1": either
# a dice group (with its own optional keep-highest/keep-lowest) or a bare
# constant. Whitespace is tolerated around the sign the same way _PATTERN
# tolerates it around the trailing modifier, but not inside a token (so
# "3 d 6" still fails, matching the single-group rules).
_TERM_PATTERN = re.compile(
    r"""
    \s*
    (?P<sign>[+-])?
    \s*
    (?:
        (?P<count>\d*)
        d
        (?P<sides>\d+|%)
        (?:\s*(?P<keep_mode>k[hl])(?P<keep_count>\d+))?
        |
        (?P<constant>\d+)
    )
    \s*
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


@dataclass(frozen=True)
class Group:
    """One signed dice group within a multi-group Expression, e.g. the
    "+2d4" in "3d6+2d4".
    """

    sign: int  # 1 or -1
    count: int
    sides: int
    keep: Optional[Keep] = None


@dataclass(frozen=True)
class Expression:
    """A parsed multi-group dice expression, e.g. "3d6+2d4-1"."""

    groups: Tuple[Group, ...]
    modifier: int = 0


def parse(text: str) -> Union[Roll, Expression]:
    """Parse dice notation into a Roll or, for multi-group notation, an
    Expression.

    Examples: "d20", "3d6", "3d6+2", "4d6kh3" (roll 4d6, keep the
    highest 3), "d%" (percentile die, equivalent to d100), "3d6+2d4"
    (multiple dice groups, returned as an Expression rather than a Roll).
    """
    match = _PATTERN.match(text)
    if match:
        return _build_roll(match)
    return _parse_expression(text)


def _build_roll(match: "re.Match") -> Roll:
    count = int(match["count"]) if match["count"] else 1
    if count < 1:
        raise ParseError("dice count must be at least 1")

    sides = 100 if match["sides"] == "%" else int(match["sides"])
    if sides < 1:
        raise ParseError("a die must have at least 1 side")

    keep = _build_keep(match, count)

    modifier_text = match["modifier"]
    modifier = int(modifier_text.replace(" ", "")) if modifier_text else 0

    return Roll(count=count, sides=sides, modifier=modifier, keep=keep)


def _build_keep(match: "re.Match", count: int) -> Optional[Keep]:
    if not match["keep_mode"]:
        return None
    keep_count = int(match["keep_count"])
    if keep_count < 1:
        raise ParseError("keep count must be at least 1")
    if keep_count > count:
        raise ParseError(f"cannot keep {keep_count} dice out of {count} rolled")
    mode = "highest" if match["keep_mode"][1].lower() == "h" else "lowest"
    return Keep(mode, keep_count)


def _parse_expression(text: str) -> Expression:
    groups = []
    modifier = 0
    term_count = 0
    pos = 0
    length = len(text)

    while pos < length:
        match = _TERM_PATTERN.match(text, pos)
        if not match:
            raise ParseError(f"invalid dice notation: {text!r}")

        sign = -1 if match["sign"] == "-" else 1
        if match["constant"] is not None:
            modifier += sign * int(match["constant"])
        else:
            count = int(match["count"]) if match["count"] else 1
            if count < 1:
                raise ParseError("dice count must be at least 1")
            sides = 100 if match["sides"] == "%" else int(match["sides"])
            if sides < 1:
                raise ParseError("a die must have at least 1 side")
            keep = _build_keep(match, count)
            groups.append(Group(sign=sign, count=count, sides=sides, keep=keep))

        term_count += 1
        pos = match.end()

    # A single term here means either a bare constant ("5") or a single
    # signed dice group ("-3d6") -- both already got a fair shot at the
    # simpler single-group pattern above and were rejected there, so
    # treat them as invalid rather than silently accepting them here.
    if term_count < 2 or not groups:
        raise ParseError(f"invalid dice notation: {text!r}")

    return Expression(groups=tuple(groups), modifier=modifier)
