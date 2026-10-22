"""Phase 10: empirical functions (build guide Part 8, E1-E6)."""
import unittest

from tests.helpers import TableMixin, compile_full, current_phase

E = ('unit kg\nunit g = 0.001 kg\nunit W\nunit s\nunit m\n'
     'empirical fn metabolic(mass: kg) -> W\n  return 3.4 * mass ^ 0.75\nend\n')
T = 'unit K\nunit degC = 1 K offset 273.15\n'


@unittest.skipIf(current_phase() < 10, 'phase 10')
class Empirical(TableMixin, unittest.TestCase):
    def test_rows(self):
        self.run_table([
            (E + 'print(metabolic(4000 g))', '9.616652224 W'),
            (E + 'let cat = 4000 g\nlet p: W = metabolic(cat)\nprint(p)', '9.616652224 W'),
            (E + 'empirical fn same(mass: kg) -> W\n  return mass\nend\nprint(same(4000 g))', '4 W'),
            (E + 'empirical fn same(mass: g) -> W\n  return mass\nend\nprint(same(4 kg))', '4000 W'),
            (E + 'empirical fn f(x) -> W\n  return x\nend', '!E1'),
            (E + 'empirical fn f(x: kg)\n  return x\nend', '!E1'),
            (E + 'empirical fn f(x: kg) -> W\n  return 3.4 kg * x\nend', '!E4'),
            (E + 'empirical fn f(x: kg) -> W\n  let k: kg = 2\n  return x\nend', '!E4'),
            (E + 'empirical fn f(x: kg) -> W\n  return x * kg\nend', '!E4'),
            (E + 'empirical fn f(x: kg) -> W\n  print(x in kg)\n  return x\nend', '!E4'),
            (E + 'fn h(a)\n  return a\nend\nempirical fn f(x: kg) -> W\n  return h(x)\nend', '!E5'),
            (E + 'empirical fn f(x: kg) -> W\n  return metabolic(x)\nend', '!E5'),
            (E + 'empirical fn f(x: kg) -> W\n  return sin(x) + x ^ 0.75 + 2 ^ x\nend\nprint(f(1 kg))',
             '3.841470985 W'),
            (E + 'empirical fn f(x: kg) -> W\n  if x > 1\n    return x\n  end\nend', '!S8'),
            (E + 'print(metabolic(5 s))', '!U9'),
            (E + 'print(metabolic(1 kg, 2 kg))', '!S4'),
            (E + 'let cat = 4 kg\nprint(metabolic(cat) + 1 kg)', '!U6'),
            (E + 'let cat = 4 kg\nempirical fn f(x: kg) -> W\n  return cat\nend', '!D8'),
            (E + 'fn outer(x: kg) -> W\n  return metabolic(x)\nend\nprint(outer(4 kg))', '9.616652224 W'),
            ('unit kg\nunit W\nprint(early(2 kg))\nempirical fn early(x: kg) -> W\n  return x * 2\nend', '4 W'),
            ('unit kg\nunit W\nempirical fn f(x: kg) -> W\n  return "hi"\nend', '!S7'),
            ('empirical fn s1(a: rad) -> 1\n  return sin(a)\nend\nprint(s1(30 deg))', '0.5'),
        ])

    def test_kinds_at_the_edge(self):
        K = ('unit kg\nunit m\nunit s\nunit N = kg * m / s^2\nkind torque\nkind energy\n'
             'empirical fn f(e: N * m of energy) -> N * m of energy\n  return e\nend\n')
        self.run_table([
            (K + 'let tau: N * m of torque = 1 N * m\nprint(f(tau))', '!K5'),
            (K + 'print(f(3 N * m))', '3 N * m'),
        ])

    def test_offsets_at_the_edge_E6(self):
        self.run_table([
            (T + 'empirical fn c(t: degC) -> 1\n  return t\nend\nprint(c(20 degC))', '20'),
            (T + 'empirical fn c(t: degC) -> 1\n  return t\nend\nprint(c(5 delta degC))', '!T8'),
            (T + 'unit kg\nempirical fn r(x: kg) -> degC\n  return 20\nend\nprint(r(1 kg))', '20 degC'),
            (T + 'unit kg\nempirical fn r(x: kg) -> degC\n  return 20\nend\nprint(r(1 kg) + r(1 kg))', '!T3'),
            (T + 'unit kg\nempirical fn r(x: kg) -> degC\n  return 20\nend\nprint(kelvin(r(1 kg)))', '293.15 K'),
        ])

    def test_generated_edges(self):
        code, errors, _ = compile_full(E + 'empirical fn mg(mass: g) -> W\n  return mass\nend\n'
                                           'let cat = 4 kg\nprint(mg(cat))')
        self.assertEqual(errors, [])
        self.assertIn('mg((cat / 0.001))', code)
        self.assertIn('def mg(mass):\n    return mass', code)
        code, errors, _ = compile_full(T + 'empirical fn c(t: degC) -> degC\n  return t\nend\nprint(c(20 degC))')
        self.assertIn('(c((293.15 - 273.15)) + 273.15)', code)


if __name__ == '__main__':
    unittest.main()
