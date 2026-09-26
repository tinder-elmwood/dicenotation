"""Parsing for tabletop dice notation strings such as "3d6+2" or "4d6kh3"."""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, Union

# count is optional (defaults to 1, as in "d20"). sides is digits or "%"
# for d100. The exploding marker "!", keep-highest/keep-lowest (or the
# "adv"/"dis" shorthand for it), and the trailing modifier are all
# optional. Whitespace is tolerated anywhere a human might type it.
_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<count>\d*)
    d
    (?P<sides>\d+|%)
    \s*
    (?P<explode>!)?
    \s*
    (?:
        (?P<keep_mode>k[hl])(?P<keep_count>\d+)
        |
        (?P<adv_dis>adv|dis)
    )?
    \s*
    (?P<modifier>[+-]\s*\d+)?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# One signed term in a multi-group expression such as "3d6+2d4-1": either
# a dice group (with its own optional exploding marker and keep-highest/
# keep-lowest) or a bare constant. Whitespace is tolerated around the sign
# the same way _PATTERN tolerates it around the trailing modifier, but not
# inside a token (so "3 d 6" still fails, matching the single-group rules).
_TERM_PATTERN = re.compile(
    r"""
    \s*
    (?P<sign>[+-])?
    \s*
    (?:
        (?P<count>\d*)
        d
        (?P<sides>\d+|%)
        \s*
        (?P<explode>!)?
        (?:
            \s*(?P<keep_mode>k[hl])(?P<keep_count>\d+)
            |
            \s*(?P<adv_dis>adv|dis)
        )?
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
    explode: bool = False


@dataclass(frozen=True)
class Group:
    """One signed dice group within a multi-group Expression, e.g. the
    "+2d4" in "3d6+2d4".
    """

    sign: int  # 1 or -1
    count: int
    sides: int
    keep: Optional[Keep] = None
    explode: bool = False


@dataclass(frozen=True)
class Expression:
    """A parsed multi-group dice expression, e.g. "3d6+2d4-1"."""

    groups: Tuple[Group, ...]
    modifier: int = 0


def parse(text: str) -> Union[Roll, Expression]:
    """Parse dice notation into a Roll or, for multi-group notation, an
    Expression.

    Examples: "d20", "3d6", "3d6+2", "4d6kh3" (roll 4d6, keep the
    highest 3), "d%" (percentile die, equivalent to d100), "4d6!" (each
    die that rolls its max value is rolled again and the results added
    together), "d20adv" (roll d20 twice, keep the higher -- shorthand
    for "2d20kh1"), "d20dis" (shorthand for "2d20kl1"), "3d6+2d4"
    (multiple dice groups, returned as an Expression rather than a
    Roll).
    """
    match = _PATTERN.match(text)
    if match:
        return _build_roll(match)
    return _parse_expression(text)


def _build_roll(match: "re.Match") -> Roll:
    count, keep = _resolve_count_and_keep(match)

    sides = 100 if match["sides"] == "%" else int(match["sides"])
    if sides < 1:
        raise ParseError("a die must have at least 1 side")

    explode = _build_explode(match, sides)

    modifier_text = match["modifier"]
    modifier = int(modifier_text.replace(" ", "")) if modifier_text else 0

    return Roll(count=count, sides=sides, modifier=modifier, keep=keep, explode=explode)


def _build_explode(match: "re.Match", sides: int) -> bool:
    if not match["explode"]:
        return False
    if sides == 1:
        raise ParseError("a d1 would explode forever, since every roll is the max")
    return True


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


def _resolve_count_and_keep(match: "re.Match") -> Tuple[int, Optional[Keep]]:
    """Work out the actual dice count and keep filter for a match, folding
    in the "adv"/"dis" shorthand: each is a single die rolled twice, with
    the better ("adv") or worse ("dis") of the two kept. It is meaningless
    with an explicit count other than 1 (roll "3d20adv" would have to mean
    either 3 dice or 2 -- reject it rather than guess).
    """
    count_text = match["count"]
    count = int(count_text) if count_text else 1
    if count < 1:
        raise ParseError("dice count must be at least 1")

    if match["adv_dis"]:
        if count_text and count != 1:
            raise ParseError(
                "advantage/disadvantage rolls a single die twice; "
                f"an explicit count of {count} does not make sense with it"
            )
        mode = "highest" if match["adv_dis"].lower() == "adv" else "lowest"
        return 2, Keep(mode, 1)

    return count, _build_keep(match, count)


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
            count, keep = _resolve_count_and_keep(match)
            sides = 100 if match["sides"] == "%" else int(match["sides"])
            if sides < 1:
                raise ParseError("a die must have at least 1 side")
            explode = _build_explode(match, sides)
            groups.append(
                Group(sign=sign, count=count, sides=sides, keep=keep, explode=explode)
            )

        term_count += 1
        pos = match.end()

    # A single term here means either a bare constant ("5") or a single
    # signed dice group ("-3d6") -- both already got a fair shot at the
    # simpler single-group pattern above and were rejected there, so
    # treat them as invalid rather than silently accepting them here.
    if term_count < 2 or not groups:
        raise ParseError(f"invalid dice notation: {text!r}")

    return Expression(groups=tuple(groups), modifier=modifier)
