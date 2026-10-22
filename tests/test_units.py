"""Phase 3: build guide Part 4 edge cases and the property tests."""
import random
import unittest

from unitsafe.units import (UnitSpec, describe, div, half, label, make, mul, power, spec_mul,
                            spec_div, spec_pow)

M = (('m', 1),)
S = (('s', 1),)
KG = (('kg', 1),)
PER_S = (('s', -1),)
M_PER_S = make({'m': 1, 's': -1})


class UnitTableEdgeCases(unittest.TestCase):
    def test_rows(self):
        self.assertEqual(mul(M, make({'m': -1})), ())
        self.assertEqual(div(M_PER_S, M_PER_S), ())
        self.assertEqual(power(M_PER_S, 0), ())
        self.assertEqual(power(S, -1), PER_S)
        self.assertEqual(half(make({'m': 2, 's': -2})), M_PER_S)
        self.assertIsNone(half(M))
        self.assertEqual(half(make({'s': -2})), PER_S)
        self.assertIsNone(half(PER_S))
        self.assertEqual(half(()), ())
        self.assertEqual(label(()), '')
        self.assertEqual(label(PER_S), '1 / s')
        self.assertEqual(label(make({'kg': 1, 'm': 2, 's': -2})), 'kg * m^2 / s^2')
        self.assertEqual(label(make({'kg': 1, 'm': -1, 's': -2})), 'kg / (m * s^2)')
        self.assertEqual(make({'m': 1, 'K': 1}), (('K', 1), ('m', 1)))
        self.assertEqual(describe(()), 'no unit')

    def test_spec_factors_C5(self):
        km = UnitSpec(M, 1000.0)
        h = UnitSpec(S, 3600.0)
        self.assertAlmostEqual(spec_div(km, h).factor, 1000 / 3600)
        self.assertEqual(spec_mul(km, h).table, make({'m': 1, 's': 1}))
        self.assertEqual(spec_pow(km, 2).factor, 1e6)


class UnitTableProperties(unittest.TestCase):
    def random_tables(self, n=500):
        rng = random.Random(42)
        for _ in range(n):
            yield (make({b: rng.randint(-3, 3) for b in ('m', 's', 'kg')}),
                   make({b: rng.randint(-3, 3) for b in ('m', 's', 'kg')}))

    def test_properties(self):
        for a, b in self.random_tables():
            self.assertEqual(div(mul(a, b), b), a)          # 1
            self.assertEqual(mul(a, b), mul(b, a))          # 2
            self.assertEqual(power(a, 2), mul(a, a))        # 3
            self.assertEqual(half(power(a, 2)), a)          # 4
            self.assertEqual(power(a, 0), ())               # 5
            self.assertEqual(mul(a, ()), a)


if __name__ == '__main__':
    unittest.main()
