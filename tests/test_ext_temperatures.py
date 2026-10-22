"""Phase 9: temperatures (build guide Part 7, T1-T8, D13)."""
import unittest

from tests.helpers import TableMixin, current_phase, outcome
from tests.test_checker import messages

T = ('unit m\nunit K\nunit s\nunit degC = 1 K offset 273.15\n'
     'unit degF = 0.5555555555555556 K offset 255.37222222222223\n')


@unittest.skipIf(current_phase() < 9, 'phase 9')
class Temperatures(TableMixin, unittest.TestCase):
    def test_rows(self):
        self.run_table([
            (T + 'print(20 degC + 5 delta degC)', '298.15 K'),
            (T + 'print(20 degC + 5 delta degC in degC)', '25 degC'),
            (T + 'print(5 delta degC + 20 degC in degC)', '25 degC'),
            (T + 'print(5 delta degC - 20 degC)', '!T3'),
            (T + 'print(25 degC - 20 degC)', '5 K'),
            (T + 'print(25 degC - 20 degC in delta degC)', '5 delta degC'),
            (T + 'print(20 degC + 20 degC)', '!T3'),
            (T + 'print(20 degC * 2)', '!T5'),
            (T + 'let t = 20 degC\nprint(t * 2)', '!T3'),
            (T + 'let t = 20 degC\nprint(-t)', '!T3'),
            (T + 'let t = 20 degC\nprint(sqrt(t))', '!T3'),
            (T + 'let t = 20 degC\nprint(t ^ 2)', '!T3'),
            (T + 'print(20 degC > 50 degF)', 'True'),
            (T + 'print(20 degC > 5 delta degC)', '!T3'),
            (T + 'let t = 20 degC\nprint(t)', '293.15 K'),
            (T + 'let t: degC = 20 degC\nprint(t)', '20 degC'),
            (T + 'let t: degC = 20 degC\nprint(t in degF)', '68 degF'),
            (T + 'let t: degC = 20 degC\nprint(t in K)', '293.15 K'),
            (T + 'let diff = 25 degC - 20 degC\nprint(diff in degF)', '!T6'),
            (T + 'let t = 20 degC\nprint(t in delta degF)', '!T6'),
            (T + 'print(10 degC / s)', '!T5'),
            (T + 'print(10 delta degC / s)', '10 K / s'),
            (T + 'print(degC)', '!T5'),
            (T + 'print(5 delta m)', '!T2'),
            (T + 'let x: delta m = 1 m', '!T2'),
            (T + 'print(kelvin(20 degC) * 2)', '586.3 K'),
            (T + 'print(kelvin(5 delta degC))', '!D13'),
            (T + 'let t: degC = 5 delta degC', '!T8'),
            (T + 'let t: delta degC = 20 degC', '!T8'),
            (T + 'let t: K = 20 degC', '!T8'),
            (T + 'unit degR = 1 degC offset 1', '!T1'),
            (T + 'unit X = 1 K * s offset 1', '!T1'),
            (T + 'print(5 degC^2)', '!T5'),
            (T + 'let a: degC / s = 1 K / s', '!T5'),
            (T + 'print(20 degC + 293 K in degC)', '313 degC'),
            (T + 'let morning: degC = 15 degC\nlet noon: degC = morning + 5 delta degC\nprint(noon - morning in delta degF)',
             '9 delta degF'),
            (T + 'fn warm(t: degC) -> degC\n  return t + 2 delta degC\nend\nprint(warm(20 degC))', '22 degC'),
        ])

    def test_messages(self):
        self.assertEqual(messages(T + 'print(20 degC + 20 degC)'), ['cannot add two temperature readings'])
        self.assertEqual(messages(T + 'let t = 20 degC\nprint(t * 2)'),
                         ['cannot multiply a reading; convert first with kelvin(...)'])
        self.assertEqual(messages(T + 'print(degC)'), ['degC alone is not a value; write 1 degC or 1 delta degC'])

    def test_equality_of_converted_floats(self):          # float note: either answer is possible
        self.assertIn(outcome(T + 'print(0 degC == 32 degF)'), ('True', 'False'))


if __name__ == '__main__':
    unittest.main()
