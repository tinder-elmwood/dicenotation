import unittest

from dicenotation import Keep, ParseError, Roll, parse


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
    ]

    def test_parse_rejects(self):
        for text in self.CASES:
            with self.subTest(text=text):
                with self.assertRaises(ParseError):
                    parse(text)


if __name__ == "__main__":
    unittest.main()
