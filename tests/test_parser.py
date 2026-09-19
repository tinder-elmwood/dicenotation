import unittest

from dicenotation import Expression, Group, Keep, ParseError, Roll, parse


class ParseValidTests(unittest.TestCase):
    # (input text, expected Roll)
    CASES = [
        ("d20", Roll(count=1, sides=20)),
        ("1d20", Roll(count=1, sides=20)),
        ("3d6", Roll(count=3, sides=6)),
        ("3d6+2", Roll(count=3, sides=6, modifier=2)),
        ("3d6-2", Roll(count=3, sides=6, modifier=-2)),
        (" 3d6 + 2 ", Roll(count=3, sides=6, modifier=2)),
        ("D20", Roll(count=1, sides=20)),
        ("d%", Roll(count=1, sides=100)),
        ("1d20+0", Roll(count=1, sides=20, modifier=0)),
        ("4d6kh3", Roll(count=4, sides=6, keep=Keep("highest", 3))),
        ("4d6kl1", Roll(count=4, sides=6, keep=Keep("lowest", 1))),
        ("4D6KH3", Roll(count=4, sides=6, keep=Keep("highest", 3))),
        ("2d20kh1+5", Roll(count=2, sides=20, modifier=5, keep=Keep("highest", 1))),
        ("d6!", Roll(count=1, sides=6, explode=True)),
        ("4d6!", Roll(count=4, sides=6, explode=True)),
        (
            "4d6!kh3",
            Roll(count=4, sides=6, keep=Keep("highest", 3), explode=True),
        ),
        (
            "4d6! kh3 +1",
            Roll(count=4, sides=6, modifier=1, keep=Keep("highest", 3), explode=True),
        ),
    ]

    def test_parse(self):
        for text, expected in self.CASES:
            with self.subTest(text=text):
                self.assertEqual(parse(text), expected)


class ParseInvalidTests(unittest.TestCase):
    # awkward malformed inputs a parser has to reject cleanly
    CASES = [
        "",
        "   ",
        "abc",
        "d",
        "3d",
        "d0",
        "0d6",
        "-3d6",
        "3d6k",
        "3d6kh",
        "3d6kh0",
        "3d6kh5",  # asks to keep more dice than were rolled
        "3d6++2",
        "3d6+",
        "3 d 6",  # space between count and "d" is not tolerated
        "5",  # a bare constant is not a dice expression
        "5+3",  # arithmetic with no dice group at all
        "3d6+2d4kh5",  # bad keep count in the second group
        "3 d 6+2d4",
        "3d6+2d",
        "d1!",  # a one-sided die would explode forever
        "3d6!!",
        "3d6+2d1!",  # the second group's d1 would explode forever
    ]

    def test_parse_rejects(self):
        for text in self.CASES:
            with self.subTest(text=text):
                with self.assertRaises(ParseError):
                    parse(text)


class ParseMultiGroupTests(unittest.TestCase):
    # (input text, expected Expression)
    CASES = [
        (
            "3d6+2d4",
            Expression(groups=(Group(1, 3, 6), Group(1, 2, 4))),
        ),
        (
            "3d6-2d4",
            Expression(groups=(Group(1, 3, 6), Group(-1, 2, 4))),
        ),
        (
            "3d6+2d4+2",
            Expression(groups=(Group(1, 3, 6), Group(1, 2, 4)), modifier=2),
        ),
        (
            " 3d6 + 2d4 - 1 ",
            Expression(groups=(Group(1, 3, 6), Group(1, 2, 4)), modifier=-1),
        ),
        (
            "1d20kh1+2d4kl1",
            Expression(
                groups=(
                    Group(1, 1, 20, Keep("highest", 1)),
                    Group(1, 2, 4, Keep("lowest", 1)),
                )
            ),
        ),
        (
            "4d6!+2d4",
            Expression(
                groups=(
                    Group(1, 4, 6, explode=True),
                    Group(1, 2, 4),
                )
            ),
        ),
        (
            "4d6!kh2+2d4kl1",
            Expression(
                groups=(
                    Group(1, 4, 6, Keep("highest", 2), explode=True),
                    Group(1, 2, 4, Keep("lowest", 1)),
                )
            ),
        ),
    ]

    def test_parse_multi_group(self):
        for text, expected in self.CASES:
            with self.subTest(text=text):
                self.assertEqual(parse(text), expected)


if __name__ == "__main__":
    unittest.main()
