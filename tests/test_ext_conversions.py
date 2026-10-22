"""Phase 6: conversions and nicknames (build guide Part 7, C1-C6, N1-N4, D11)."""
import unittest

from tests.helpers import TableMixin, current_phase

U = 'unit m\nunit s\nunit kg\nunit km = 1000 m\nunit h = 3600 s\n'


@unittest.skipIf(current_phase() < 6, 'phase 6')
class Conversions(TableMixin, unittest.TestCase):
    def test_rows(self):
        self.run_table([
            (U + 'print(1 km + 500 m)', '1500 m'),
            (U + 'print(1 km + 500 m in km)', '1.5 km'),
            (U + 'let d: km = 1500 m\nprint(d)', '1.5 km'),
            (U + 'print(5 km)', '5 km'),
            (U + 'print(5 km in m)', '5000 m'),
            (U + 'print(1 km^2 in m^2)', '1000000 m^2'),
            ('unit m\nunit L = 0.001 m^3\nprint(2 L in m^3)', '0.002 m^3'),
            (U + 'unit mile = 1.609 km\nprint(1 mile in m)', '1609 m'),
            (U + 'print(0.1 km + 0.2 km in km)', '0.3 km'),
            (U + 'print(150 km / 2 h in km / h)', '75 km / h'),
            (U + 'print(150 km / 2 h)', '20.83333333 m / s'),
            (U + 'let d = 150 km\nfn speed(x: km, t: h) -> km / h\n  return x / t\nend\nprint(speed(d, 2 h))',
             '75 km / h'),
            (U + 'unit km = 1000 m', '!C3'),
            ('unit m\nunit km = 0 m', '!C3'),
            ('unit m\nunit km = -5 m', '!C3'),
            ('unit km = 1000 m\nunit m', '!C1'),
            (U + 'let d = 5 km\nprint(d in s)', '!C6'),
            (U + 'print("a" in km)', '!C6'),
            (U + 'let x: km = 5 s', '!U8'),
            (U + 'print(2 m in 1)', '!C6'),
        ])

    def test_nicknames(self):
        N = 'unit kg\nunit m\nunit s\nunit N = kg * m / s^2\n'
        self.run_table([
            (N + 'print(5 N + 2 kg * m / s^2)', '7 N'),                       # N3b: one match
            (N + 'unit newton = kg * m / s^2\nprint(5 N + 2 N)', '7 kg * m / s^2'),   # N3b: two matches
            ('unit s\nunit Hz = 1 / s\nprint(1 / 2 s)', '0.5 Hz'),
            ('unit s\nunit Hz = 1 / s\nunit Bq = 1 / s\nprint(1 / 2 s)', '0.5 1 / s'),
            ('unit m\nunit km = 1000 m\nprint(2 km + 1 m)', '2001 m'),         # factor 1000: never a nickname
            (N + 'let F: N = 2 kg * 3 m / s^2\nprint(F)', '6 N'),
            ('unit s\nunit Hz = 1 / s\nprint(50 Hz)', '50 Hz'),
            ('unit s\nunit Hz = 1 / s\nunit kHz = 1000 Hz\nprint(2 kHz in Hz)', '2000 Hz'),
            (N + 'unit J = N * m\nlet w: J = 2 N * 3 m\nprint(w)', '6 J'),
            ('unit kg\nunit N = kg * foo', '!C1'),
            (N + 'let N = 5', '!U2'),
            ('unit m\nunit A2 = (m / s)^2', '!C1'),
            ('unit m\nunit s\nunit A2 = (m / s)^2\nprint(4 A2 in m^2 / s^2)', '4 m^2 / s^2'),
        ])

    def test_currency_D25(self):
        self.run_table([
            ('unit INR\nunit USD\nlet rate = 83.2 INR / USD\nprint(20 USD * rate in INR)', '1664 INR'),
            ('unit INR\nunit USD = 83.2 INR\nprint(20 USD + 100 INR)', '1764 INR'),
        ])


if __name__ == '__main__':
    unittest.main()
