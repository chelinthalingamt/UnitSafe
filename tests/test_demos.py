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


if __name__ == '__main__':
    unittest.main()
