import random
import unittest

from dicenotation import Keep, Roll, roll


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


if __name__ == "__main__":
    unittest.main()
