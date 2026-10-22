"""Phase 7: angles (build guide Part 7, A1-A6, D12, D22)."""
import unittest

from tests.helpers import TableMixin, current_phase
from tests.test_checker import messages

U = 'unit m\nunit s\nunit Hz = 1 / s\nlet r = 2 m\nlet theta = 30 deg\n'


@unittest.skipIf(current_phase() < 7, 'phase 7')
class Angles(TableMixin, unittest.TestCase):
    def test_rows(self):
        self.run_table([
            ('print(sin(90))', '!A3'),
            ('print(sin(90 deg))', '1'),
            (U + 'print(sin(2 * theta))', '0.8660254038'),
            (U + 'print(sin(theta ^ 2))', '!A3'),
            (U + 'let arc: m = r * theta\nprint(arc)', '1.047197551 m'),
            (U + 'let arc = r * theta\nprint(arc)', '1.047197551 m * rad'),
            (U + 'print(r * theta in m)', '1.047197551 m'),
            (U + 'let f = 50 Hz\nlet w: rad / s = 2 * f\nprint(w)', '100 rad / s'),
            (U + 'print(50 Hz + 314 rad / s)', '!U6'),
            ('print(asin(0.5))', '0.5235987756 rad'),
            ('unit m\nprint(asin(1 m))', '!A4'),
            ('unit m\nprint(atan2(3 m, 4 m) in deg)', '36.86989765 deg'),
            ('unit m\nunit s\nprint(atan2(3 m, 4 s))', '!A4'),
            ('print(1 rad in deg)', '57.29577951 deg'),
            ('print(180 deg in rad)', '3.141592654 rad'),
            ('unit rad', '!C3'),
            ('let rad = 5', '!U2'),
            (U + 'print(theta / theta)', '1'),
            ('print(sin(pi))', '!A3'),
            ('print(sin(pi * rad))', '1.224646799e-16'),
            ('let x = 1\nprint(cos(x))', '!A3'),
            ('print(cos(0 rad))', '1'),
            ('print(deg)', '0.01745329252 rad'),
            (U + 'print(theta in deg)', '30 deg'),
            ('print(asin(0.5) in deg)', '30 deg'),
        ])

    def test_messages(self):
        self.assertEqual(messages('print(sin(90))'),
                         ['sin needs an angle but got a plain number; write 90 deg or 90 rad'])
        self.assertEqual(messages('print(sin(pi))'),
                         ['sin needs an angle but got a plain number; write pi * rad'])
        self.assertEqual(messages('unit rad'), ["'rad' is built in"])


if __name__ == '__main__':
    unittest.main()
