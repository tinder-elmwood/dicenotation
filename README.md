# dicenotation

A small library for parsing and rolling tabletop dice notation: strings
like `3d6+2`, `d20`, or `4d6kh3` (roll four six-sided dice, keep the
highest three — the classic D&D ability score method).

Most of these libraries either hardcode a fixed set of roll types or
make you write your own regex every time a game needs a slightly
different notation. This one splits parsing from rolling, so you can
inspect or reuse a parsed expression, and it takes an injectable RNG so
roll outcomes can be tested deterministically instead of only checking
that a number came back "in range".

## Usage

```python
from dicenotation import roll, parse

result = roll("3d6+2")
print(result.rolls)   # e.g. (4, 1, 6)
print(result.total)   # e.g. 13

# keep-highest / keep-lowest
result = roll("4d6kh3")
print(result.rolls)   # all four dice, e.g. (2, 5, 5, 1)
print(result.kept)    # the three that counted, e.g. (2, 5, 5)
print(result.total)   # 12

# parse once, roll many times
ability_score = parse("4d6kh3")
scores = [roll(ability_score).total for _ in range(6)]
```

For reproducible results (tests, replays, seeded games), pass your own
`random.Random`:

```python
import random
from dicenotation import roll

rng = random.Random(1234)
result = roll("2d20kh1", rng=rng)  # advantage roll
```

## Supported notation

- `NdX` — roll N dice with X sides (`N` defaults to 1: `d20` == `1d20`)
- `d%` — percentile die, equivalent to `d100`
- `NdXkhK` / `NdXklK` — keep the highest/lowest K of the N dice rolled
- a trailing `+M` or `-M` modifier, added after any keep filtering

Invalid notation (empty strings, zero-sided dice, asking to keep more
dice than were rolled, and so on) raises `dicenotation.ParseError`.

## Status

Early skeleton. Single dice groups only — no `3d6+2d4`, no exploding
dice yet. See the test suite for the exact set of notation currently
accepted and rejected.
