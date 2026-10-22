"""Phase 0: the contract files exist and the samples are complete."""
import pathlib
import unittest

from unitsafe import ast_nodes, tokens
from unitsafe.tokens import KEYWORDS, TokenType

PROGRAMS = pathlib.Path(__file__).parent / 'programs'


class ContractTests(unittest.TestCase):
    def test_all_keywords_reserved(self):           # D18 + D19/D20
        expected = {'unit', 'let', 'fn', 'return', 'print', 'if', 'else', 'while', 'end',
                    'in', 'kind', 'of', 'offset', 'delta', 'empirical',
                    'true', 'false', 'and', 'or', 'not'}
        self.assertEqual(set(KEYWORDS), expected)
        for word, tt in KEYWORDS.items():
            self.assertIsInstance(tt, TokenType)

    def test_nodes_compare_by_shape(self):
        a = ast_nodes.Number(value=1.0, text='1', line=1, col=1)
        b = ast_nodes.Number(value=1.0, text='1', line=9, col=4)
        self.assertEqual(a, b)

    def test_ten_samples_with_expected_output(self):
        samples = sorted(PROGRAMS.glob('sample*.us'))
        self.assertEqual(len(samples), 10)
        for s in samples:
            self.assertTrue(s.with_suffix('.expected').exists(), s.name)


if __name__ == '__main__':
    unittest.main()
