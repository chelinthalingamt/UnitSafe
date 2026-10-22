"""D28: use si: ... (rules SI1-SI3)."""
import unittest

from tests.helpers import TableMixin, outcome


class UseSI(TableMixin, unittest.TestCase):
    def test_rows(self):
        self.run_table([
            ('use si: m, s, kg, N\nprint(2 kg * 3 m / s^2)', '6 N'),
            ('use si: km, h\nprint(150 km / 2 h in km / h)', '75 km / h'),           # SI3: no need to list m, s
            ('use si: N\nprint(3 N)', '3 N'),
            ('use si: N, J, m\nlet w: J = 2 N * 3 m\nprint(w)', '6 J'),
            ('use si: m, s, kg, W\nprint(10 kg * m^2 / s^3)', '10 W'),
            ('use si: V, A, ohm\nprint(12 V / 2 A)', '6 ohm'),
            ('use si: L, cm\nprint(1 L in cm^3)', '1000 cm^3'),
            ('use si: g, kg\nprint(500 g + 1 kg in kg)', '1.5 kg'),
            ('use si: m, s\nlet g = 9.8 m / s^2\nprint(g)', '9.8 m / s^2'),               # g stays free
            ('use si: m\nunit ft = 0.3048 m\nprint(10 ft in m)', '3.048 m'),
            ('use si: g\nlet g = 9.8', '!U2'),
            ('use si: foo', '!SI1'),
            ('use metric: m', '!SI1'),
            ('use si: m\nunit m', '!C3'),
            ('unit m\nuse si: m', '!C3'),
            ('use si: m, m', '!C3'),
            ('if true\n  use si: m\nend', '!S11'),
            ('use si m', '!P6'),
            ('use si:', '!P6'),
            ('let use = 1', '!P6'),
        ])

    def test_temperatures_are_offset_aware(self):
        self.run_table([
            ('use si: degC, degF\nlet t: degC = 20 degC\nprint(t in degF)', '68 degF'),
            ('use si: degC, degF\nlet t: degF = 98.6 degF\nprint(t in degC)', '37 degC'),
            ('use si: degC\nprint(20 degC + 20 degC)', '!T3'),
            ('use si: degC\nprint(20 degC * 2)', '!T5'),
            ('use si: degC, K\nprint(kelvin(20 degC))', '293.15 K'),
            ('use si: degC\nprint(25 degC - 20 degC in delta degC)', '5 delta degC'),
        ])
        self.assertEqual(outcome('use si: degC, degF\nlet t: degC = read(degC)\nprint(t)', '68 degF\n'), '20 degC')


if __name__ == '__main__':
    unittest.main()
