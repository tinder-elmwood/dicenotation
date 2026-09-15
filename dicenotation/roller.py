"""Rolling parsed dice expressions."""

import random
from dataclasses import dataclass
from typing import Optional, Tuple, Union

from .parser import Expression, Group, Keep, Roll, parse

_DiceSpec = Union[str, Roll, Expression]


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


@dataclass(frozen=True)
class GroupResult:
    """The outcome of rolling one signed Group within an Expression."""

    sign: int
    rolls: Tuple[int, ...]
    kept: Tuple[int, ...]


@dataclass(frozen=True)
class ExpressionResult:
    """The outcome of rolling a multi-group Expression: each group's own
    result plus the flat modifier and the combined total.
    """

    groups: Tuple[GroupResult, ...]
    modifier: int
    total: int


def roll(
    spec: _DiceSpec, rng: "random.Random" = random
) -> Union[RollResult, ExpressionResult]:
    """Roll a dice expression, given either notation text or a value
    already returned by parse() (a Roll for a single dice group, or an
    Expression for multi-group notation like "3d6+2d4").

    Pass an rng (anything with a randint(a, b) method, such as a seeded
    random.Random) to get reproducible results, e.g. for tests.
    """
    if isinstance(spec, str):
        spec = parse(spec)

    if isinstance(spec, Expression):
        return _roll_expression(spec, rng)
    return _roll_single(spec, rng)


def _roll_dice(
    count: int, sides: int, keep: Optional[Keep], rng
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    rolls = tuple(rng.randint(1, sides) for _ in range(count))

    if keep is None:
        return rolls, rolls

    by_value = sorted(
        range(len(rolls)),
        key=lambda i: rolls[i],
        reverse=(keep.mode == "highest"),
    )
    kept_indices = sorted(by_value[: keep.count])
    kept = tuple(rolls[i] for i in kept_indices)
    return rolls, kept


def _roll_single(spec: Roll, rng) -> RollResult:
    rolls, kept = _roll_dice(spec.count, spec.sides, spec.keep, rng)
    total = sum(kept) + spec.modifier
    return RollResult(rolls=rolls, kept=kept, modifier=spec.modifier, total=total)


def _roll_group(group: Group, rng) -> GroupResult:
    rolls, kept = _roll_dice(group.count, group.sides, group.keep, rng)
    return GroupResult(sign=group.sign, rolls=rolls, kept=kept)


def _roll_expression(expr: Expression, rng) -> ExpressionResult:
    group_results = tuple(_roll_group(group, rng) for group in expr.groups)
    total = expr.modifier + sum(g.sign * sum(g.kept) for g in group_results)
    return ExpressionResult(groups=group_results, modifier=expr.modifier, total=total)
