import random
import unittest

from dicenotation import Expression, Group, Keep, Roll, roll


class _FixedRng:
    """Hands out a scripted sequence of "random" values instead of real
    ones, so keep-highest/keep-lowest ordering can be tested exactly.
    """

    def __init__(self, values):
        self._values = list(values)

    def randint(self, a, b):
        return self._values.pop(0)


class RollerTests(unittest.TestCase):
    def test_plain_roll_stays_in_range_and_sums_correctly(self):
        rng = random.Random(1234)
        result = roll("3d6", rng=rng)
        self.assertEqual(len(result.rolls), 3)
        self.assertTrue(all(1 <= r <= 6 for r in result.rolls))
        self.assertEqual(result.kept, result.rolls)
        self.assertEqual(result.total, sum(result.rolls))

    def test_accepts_parsed_roll_as_well_as_text(self):
        spec = Roll(count=2, sides=10, modifier=3)
        result = roll(spec, rng=random.Random(42))
        self.assertEqual(len(result.rolls), 2)
        self.assertEqual(result.total, sum(result.rolls) + 3)

    def test_keep_highest_selects_the_largest_values(self):
        # rolled dice: 5, 1, 5, 2 -- keep-highest-2 should keep both 5s,
        # even though they came from different positions
        rng = _FixedRng([5, 1, 5, 2])
        spec = Roll(count=4, sides=6, keep=Keep("highest", 2))
        result = roll(spec, rng=rng)
        self.assertEqual(result.rolls, (5, 1, 5, 2))
        self.assertEqual(result.kept, (5, 5))
        self.assertEqual(result.total, 10)

    def test_keep_lowest_preserves_original_die_order(self):
        rng = _FixedRng([5, 1, 5, 2])
        spec = Roll(count=4, sides=6, keep=Keep("lowest", 2))
        result = roll(spec, rng=rng)
        self.assertEqual(result.rolls, (5, 1, 5, 2))
        # lowest two values are 1 and 2, kept in the order they were rolled
        self.assertEqual(result.kept, (1, 2))

    def test_modifier_is_applied_after_keep_filtering(self):
        rng = _FixedRng([4, 6, 2])
        spec = Roll(count=3, sides=6, keep=Keep("highest", 2), modifier=1)
        result = roll(spec, rng=rng)
        self.assertEqual(result.kept, (4, 6))
        self.assertEqual(result.total, 11)

    def test_keep_all_dice_is_a_no_op(self):
        rng = _FixedRng([3, 3, 3])
        spec = Roll(count=3, sides=6, keep=Keep("highest", 3))
        result = roll(spec, rng=rng)
        self.assertEqual(result.kept, result.rolls)

    def test_exploding_die_adds_the_extra_roll(self):
        # the first die rolls max (6) and explodes into a 4; the second
        # die rolls a plain 2 and stops
        rng = _FixedRng([6, 4, 2])
        spec = Roll(count=2, sides=6, explode=True)
        result = roll(spec, rng=rng)
        self.assertEqual(result.rolls, (10, 2))
        self.assertEqual(result.total, 12)

    def test_exploding_die_can_chain_multiple_times(self):
        # 6, 6, 6, 3 -- three max rolls in a row before finally settling
        rng = _FixedRng([6, 6, 6, 3])
        spec = Roll(count=1, sides=6, explode=True)
        result = roll(spec, rng=rng)
        self.assertEqual(result.rolls, (21,))

    def test_non_exploding_die_never_rerolls_a_max_value(self):
        rng = _FixedRng([6, 6])
        spec = Roll(count=2, sides=6)
        result = roll(spec, rng=rng)
        self.assertEqual(result.rolls, (6, 6))

    def test_exploding_interacts_with_keep_highest(self):
        # die 1 rolls 6 and explodes into 5 (total 11); die 2 rolls a
        # plain 2 -- keep-highest-1 should keep the exploded die
        rng = _FixedRng([6, 5, 2])
        spec = Roll(count=2, sides=6, keep=Keep("highest", 1), explode=True)
        result = roll(spec, rng=rng)
        self.assertEqual(result.rolls, (11, 2))
        self.assertEqual(result.kept, (11,))
        self.assertEqual(result.total, 11)


class ExpressionRollerTests(unittest.TestCase):
    def test_multi_group_totals_are_summed_across_groups(self):
        # 3d6 rolls 4, 1, 6 (sum 11); 2d4 rolls 2, 3 (sum 5)
        rng = _FixedRng([4, 1, 6, 2, 3])
        result = roll("3d6+2d4", rng=rng)
        self.assertEqual(len(result.groups), 2)
        self.assertEqual(result.groups[0].rolls, (4, 1, 6))
        self.assertEqual(result.groups[1].rolls, (2, 3))
        self.assertEqual(result.total, 16)

    def test_negative_group_is_subtracted(self):
        # 3d6 rolls to 11, 2d4 rolls to 5, then a flat +1
        rng = _FixedRng([4, 1, 6, 2, 3])
        result = roll("3d6-2d4+1", rng=rng)
        self.assertEqual(result.modifier, 1)
        self.assertEqual(result.total, 11 - 5 + 1)

    def test_keep_filtering_applies_per_group(self):
        rng = _FixedRng([5, 1, 5, 2, 3, 4])
        spec = Expression(
            groups=(
                Group(1, 4, 6, Keep("highest", 2)),
                Group(1, 2, 4),
            )
        )
        result = roll(spec, rng=rng)
        self.assertEqual(result.groups[0].kept, (5, 5))
        self.assertEqual(result.groups[1].kept, (3, 4))
        self.assertEqual(result.total, 10 + 7)

    def test_exploding_group_within_an_expression(self):
        # first group: one d6 rolls 6 and explodes into 2 (total 8);
        # second group: a plain 2d4 rolling 1, 3
        rng = _FixedRng([6, 2, 1, 3])
        spec = Expression(
            groups=(
                Group(1, 1, 6, explode=True),
                Group(1, 2, 4),
            )
        )
        result = roll(spec, rng=rng)
        self.assertEqual(result.groups[0].rolls, (8,))
        self.assertEqual(result.total, 8 + 4)


if __name__ == "__main__":
    unittest.main()
