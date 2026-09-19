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

Multiple dice groups can be combined in one expression, e.g. a damage
roll with a bonus die:

```python
result = roll("3d6+2d4+2")
print(result.groups[0].rolls)  # the 3d6, e.g. (4, 1, 6)
print(result.groups[1].rolls)  # the 2d4, e.g. (2, 3)
print(result.modifier)         # 2
print(result.total)            # sum of every kept die plus the modifier
```

`parse()` returns a `Roll` for a single dice group (as above) and an
`Expression` for multi-group notation; `roll()` accepts either, plus the
original notation text, and returns a `RollResult` or `ExpressionResult`
to match.

## Supported notation

- `NdX` — roll N dice with X sides (`N` defaults to 1: `d20` == `1d20`)
- `d%` — percentile die, equivalent to `d100`
- `NdX!` — exploding dice: any die that rolls its max value (X) is
  rolled again, and the new roll is added to it; this repeats as long
  as the die keeps coming up max, so a single die's entry in `rolls`
  can be greater than X
- `NdXkhK` / `NdXklK` — keep the highest/lowest K of the N dice rolled
- a trailing `+M` or `-M` modifier, added after any keep filtering
- multiple dice groups joined by `+`/`-`, e.g. `3d6+2d4`, each with its
  own optional exploding marker and keep filter (`1d20kh1+2d4kl1`,
  `4d6!kh3`); a `-` before a group subtracts that group's kept total
  rather than negating each die

`d1!` is rejected, since a one-sided die always rolls its max and would
explode forever.

Invalid notation (empty strings, zero-sided dice, asking to keep more
dice than were rolled, a bare number with no dice group, and so on)
raises `dicenotation.ParseError`.

## Status

Early skeleton. See the test suite for the exact set of notation
currently accepted and rejected.
