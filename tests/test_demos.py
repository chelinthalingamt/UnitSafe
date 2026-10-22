"""The review demos behave as the demo script promises."""
import pathlib
import unittest

from tests.helpers import outcome

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(path):
    return outcome((ROOT / path).read_text(encoding='utf-8'))


class Demos(unittest.TestCase):
    def test_review2(self):
        self.assertEqual(run('demo/review2/01_valid.us').splitlines()[0], 'drop from 1 m takes 0.4517539515 s')
        self.assertEqual(run('demo/review2/02_mixup.us'), '!U6@6')
        self.assertEqual(run('demo/review2/03_several_mistakes.us'), '!U9@10 U9@10 U6@11 U11@12')

    def test_review3(self):
        self.assertEqual(run('demo/review3/01_conversions.us'), 'average speed: 75 km / h')
        self.assertEqual(run('demo/review3/02_angles.us'), '!A3@3')
        self.assertEqual(run('demo/review3/03_kinds.us'), '!K3@11')
        self.assertEqual(run('demo/review3/04_temperatures.us'),
                         'noon: 20 degC = 68 degF\nit got warmer by 9 delta degF')
        self.assertEqual(run('demo/review3/05_empirical.us'), 'cat: 9.616652224 W\nmouse: 0.1808220605 W')


    def test_showcase(self):                       # expected values worked out by hand in plain Python
        self.assertEqual(run('demo/showcase/01_motion.us').splitlines(), [
            'speed: 12.5 m / s', 'stopping distance: 13.02083333 m', 'verdict: careful',
            'kinetic energy: 93750 kg * m^2 / s^2', 'track length: 314.1592654 m'])
        self.assertEqual(run('demo/showcase/02_conversions.us').splitlines(), [
            'trip time: 3.5 h', 'average speed: 68.57142857 km / h', 'force: 3000 N',
            'work: 300000 J', 'power: 15000 W = 15 kW'])
        self.assertEqual(run('demo/showcase/03_angles.us').splitlines(), [
            'ramp height: 5 m', 'ramp base: 8.660254038 m', 'roof slope: 22.61986495 deg',
            'distance rolled: 0.471238898 m', 'spin rate: 0.7853981634 rad / s'])
        self.assertEqual(run('demo/showcase/04_kinds_temperatures.us').splitlines(), [
            'wrench torque: 10 N * m', 'lifting energy: 196 J', 'body temperature: 37 degC = 98.6 degF',
            'fever: 38.5 degC', 'rise: 2.7 delta degF', 'in kelvin: 310.15 K'])
        self.assertEqual(run('demo/showcase/05_empirical.us').splitlines(), [
            'sound at 20 degC: 343.42 m / s', 'sound at 25 degC: 346.45 m / s',
            'thunder delay: 2.886419397 s', 'cat: 9.616652224 W', 'elephant: 2021.652096 W'])
        self.assertEqual(run('demo/showcase/06_money.us').splitlines(), [
            'laptop in rupees: 79040 INR', 'total cost: 80240 INR'])

    def test_input_check_D27(self):
        src = (ROOT / 'demo/showcase/07_input_check.us').read_text(encoding='utf-8')
        self.assertEqual(outcome(src, '1100 lbf * s\n'),
                         'thruster impulse (with its unit): received 4892.8 N * s\nenough to reach orbit')
        self.assertEqual(outcome(src, '1100 N * s\n'),
                         'thruster impulse (with its unit): received 1100 N * s\nnot enough')
        self.assertEqual(outcome(src, '1100 kg\n'), '!input')

    def test_use_si_and_syntax_errors(self):
        self.assertEqual(run('demo/showcase/08_use_si.us').splitlines(), [
            'energy to climb the hill: 205800 J', 'average power: 137.2 W',
            'walking pace: 10.8 km / h', 'lake water: 18 degC = 64.4 degF'])
        self.assertEqual(run('demo/review3/07_syntax_errors.us'), '!P6@4 P6@7 P6@9')

if __name__ == '__main__':
    unittest.main()
