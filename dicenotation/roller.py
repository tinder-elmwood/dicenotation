"""Rolling parsed dice expressions."""

import random
from dataclasses import dataclass
from typing import Tuple, Union

from .parser import Roll, parse

_DiceSpec = Union[str, Roll]


@dataclass(frozen=True)
class RollResult:
    """The outcome of rolling a Roll: every die rolled, the dice that were
    actually kept (after any keep-highest/keep-lowest filtering), and the
    final total including the modifier.
    """

    rolls: Tuple[int, ...]
    kept: Tuple[int, ...]
    modifier: int
    total: int


def roll(spec: _DiceSpec, rng: "random.Random" = random) -> RollResult:
    """Roll a dice expression, given either notation text or a parsed Roll.

    Pass an rng (anything with a randint(a, b) method, such as a seeded
    random.Random) to get reproducible results, e.g. for tests.
    """
    if isinstance(spec, str):
        spec = parse(spec)

    rolls = tuple(rng.randint(1, spec.sides) for _ in range(spec.count))

    if spec.keep is None:
        kept = rolls
    else:
        by_value = sorted(
            range(len(rolls)),
            key=lambda i: rolls[i],
            reverse=(spec.keep.mode == "highest"),
        )
        kept_indices = sorted(by_value[: spec.keep.count])
        kept = tuple(rolls[i] for i in kept_indices)

    total = sum(kept) + spec.modifier
    return RollResult(rolls=rolls, kept=kept, modifier=spec.modifier, total=total)
