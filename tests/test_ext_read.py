"""D27: read(...) with run-time unit validation (rules R1-R6)."""
import unittest

from tests.helpers import compile_full, outcome

U = 'unit kg\nunit m\nunit s\nunit N = kg * m / s^2\nunit lbf = 4.448 N\n'
T = ('unit K\nunit degC = 1 K offset 273.15\n'
     'unit degF = 0.5555555555555556 K offset 255.37222222222223\n')
IMPULSE = U + 'let i: N * s = read(N * s)\nprint(i)'


class Read(unittest.TestCase):
    def rows(self, rows):
        for src, typed, expected in rows:
            with self.subTest(src=src, typed=typed):
                got = outcome(src, typed + '\n' if typed is not None else '')
                if expected.startswith('!') and '@' not in expected and got.startswith('!'):
                    got = got.split('@')[0]
                self.assertEqual(got, expected, f'\n{src}\ntyped: {typed!r}')

    def test_conversion_R2(self):
        self.rows([
            (IMPULSE, '1100 lbf * s', '4892.8 N * s'),
            (IMPULSE, '1100 lbf*s', '4892.8 N * s'),
            (IMPULSE, '1100lbf * s', '4892.8 N * s'),
            (IMPULSE, '4000 N * s', '4000 N * s'),
            (IMPULSE, '4000 kg * m / s', '4000 N * s'),
            (IMPULSE, '1.5e3 N * s', '1500 N * s'),
            (IMPULSE, '-20 N * s', '-20 N * s'),
            ('unit m\nunit km = 1000 m\nlet d: km = read(m)\nprint(d)', '2.5 km', '2.5 km'),
            ('unit m\nunit s\nlet a = read(m / s^2)\nprint(a)', '9.8 m / (s * s)', '9.8 m / s^2'),
            ('let a: deg = read(rad)\nprint(a)', '90 deg', '90 deg'),
        ])

    def test_unit_required_R1(self):
        self.rows([
            (IMPULSE, '1100', '!input'),
            ('let x = read(1)\nprint(x * 2)', '21', '42'),
            ('unit m\nlet x = read(1)\nprint(x)', '5 m', '!input'),
        ])

    def test_refused_input_R3(self):
        self.rows([
            (IMPULSE, '5 kg', '!input'),
            (IMPULSE, '5 lbx * s', '!input'),
            (IMPULSE, 'abc', '!input'),
            (IMPULSE, '5 N * s extra', '!input'),
            (IMPULSE, '5 N * s^x', '!input'),
            (IMPULSE, None, '!input'),                       # no input at all
        ])

    def test_kind_kept_R4(self):
        H = ('unit kg\nunit m\nunit s\nunit N = kg * m / s^2\nkind torque\nkind energy\n'
             'unit J = N * m of energy\nlet work = 40 J\n')
        self.rows([
            (H + 'let t = read(N * m of torque)\nprint(t + work)', '5 N * m', '!K3'),
            (H + 'let e = read(J)\nprint(e + work)', '5 N * m', '45 J'),
        ])

    def test_temperatures_R5(self):
        R = T + 'let t: degC = read(degC)\nprint(t)'
        D = T + 'let d: delta degC = read(delta degC)\nprint(d)'
        self.rows([
            (R, '68 degF', '20 degC'),
            (R, '293.15 K', '20 degC'),
            (R, '20 degC', '20 degC'),
            (R, '5 delta degC', '!input'),
            (R, '20', '!input'),
            (D, '9 delta degF', '5 delta degC'),
            (D, '5 degC', '!input'),
            (D, '5 K', '5 delta degC'),
            ('unit s\n' + T + 'let r = read(K / s)\nprint(r)', '5 degC / s', '!input'),
        ])

    def test_not_in_empirical_R6(self):
        self.rows([('unit kg\nunit W\nempirical fn f(x: kg) -> W\n  return read(kg)\nend', None, '!E4')])

    def test_prompt_and_loops(self):
        self.rows([
            ('unit m\nlet d = read("distance: ", m)\nprint(d)', '3 m', 'distance: 3 m'),
        ])
        src = 'unit m\nlet i = 0\nlet total = 0 m\nwhile i < 3\n  total = total + read(m)\n  i = i + 1\nend\nprint(total)'
        self.assertEqual(outcome(src, '1 m\n2 m\n3 m\n'), '6 m')

    def test_unit_table_only_when_needed(self):
        code, _, _ = compile_full('unit m\nprint(1 m)')
        self.assertNotIn('US_UNITS', code)
        code, _, _ = compile_full('unit m\nprint(read(m))')
        self.assertIn('US_UNITS = {', code)
        self.assertIn("us_read('', {'m': 1}, 'm', False, False)", code)

    def test_parse_errors(self):
        self.rows([
            ('unit m\nprint(read())', None, '!P6'),
            ('unit m\nprint(read("x" m))', None, '!P6'),
            ('let read = 1', None, '!P6'),                   # read is a keyword now
        ])


if __name__ == '__main__':
    unittest.main()
