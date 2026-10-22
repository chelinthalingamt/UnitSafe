"""The erasure test (build guide Part 11): a compiled program prints the same numbers
as a hand-written Python version with no units at all. This is the zero-cost claim."""
import math
import pathlib
import unittest

from tests.helpers import outcome

PROGRAMS = pathlib.Path(__file__).resolve().parent / 'programs'


def g(x):
    return format(0.0 if x == 0 else x, '.10g')


def basics():                       # sample02_basics, by hand
    d, t = 120.0, 10.0
    v = d / t
    a = 9.8
    return [g(v), g(v * 4), g(5 / 5), g(2 * 5), g(a * 2)]


def falling():                      # sample03_falling, by hand
    out, h, grav = [], 1.0, 9.8
    while h < 1000:
        out.append(f'{g(h)} {g(math.sqrt(2 * h / grav))}')
        h *= 10
    return out


def conversions():                  # sample07_conversions, by hand (metres and seconds throughout)
    d, t = 150 * 1000.0, 2 * 3600.0
    return [g(d / t / (1000 / 3600)), g(d / t), g(2 * 3), g((1000 + 500) / 1000)]


def numbers(lines):
    """Keep only the numbers from each printed line."""
    out = []
    for line in lines:
        nums = [w for w in line.split() if w[0].isdigit() or w[0] == '-']
        out.append(' '.join(nums))
    return out


class Erasure(unittest.TestCase):
    def check(self, sample, hand):
        printed = outcome((PROGRAMS / sample).read_text(encoding='utf-8')).splitlines()
        self.assertEqual(numbers(printed), hand())

    def test_basics(self):
        self.check('sample02_basics.us', basics)

    def test_falling(self):
        self.check('sample03_falling.us', falling)

    def test_conversions(self):
        self.check('sample07_conversions.us', conversions)


if __name__ == '__main__':
    unittest.main()
