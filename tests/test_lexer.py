"""Phase 1: every row of build guide Part 1 'Edge cases'."""
import unittest

from unitsafe.errors import LexError
from unitsafe.lexer import tokenize
from unitsafe.tokens import TokenType as T


def types(src):
    return [t.type for t in tokenize(src)]


def err(src):
    try:
        tokenize(src)
    except LexError as e:
        return e.error
    return None


class LexerEdgeCases(unittest.TestCase):
    def test_spaces_skipped_L2(self):
        self.assertEqual(types('x   =  5'), [T.NAME, T.EQUALS, T.NUMBER, T.NEWLINE, T.EOF])

    def test_number_glued_to_name(self):
        for src in ('5kg', '5 kg'):
            toks = tokenize(src)
            self.assertEqual([t.type for t in toks[:2]], [T.NUMBER, T.NAME])
            self.assertEqual((toks[0].value, toks[1].text), (5.0, 'kg'))

    def test_scientific_D5(self):
        self.assertEqual(tokenize('1.5e3')[0].value, 1500.0)
        self.assertEqual(tokenize('2E-4')[0].value, 0.0002)
        toks = tokenize('5eV')
        self.assertEqual([(t.type, t.text) for t in toks[:2]], [(T.NUMBER, '5'), (T.NAME, 'eV')])
        toks = tokenize('2e')
        self.assertEqual([(t.type, t.text) for t in toks[:2]], [(T.NUMBER, '2'), (T.NAME, 'e')])

    def test_malformed_numbers_L5(self):
        self.assertEqual(err('3.').rule, 'L5')
        self.assertIn("'3.'", err('3.').message)
        self.assertIn("'3.4.5'", err('3.4.5').message)
        self.assertIn('separators', err('1_000').message)
        self.assertIn('too large', err('1e400').message)

    def test_leading_dot_L7(self):
        e = err('.5')
        self.assertEqual((e.rule, e.col), ('L7', 1))
        self.assertIn('0.5', e.message)

    def test_leading_zeros(self):
        self.assertEqual(tokenize('007')[0].value, 7.0)

    def test_longest_match_L3(self):
        self.assertEqual(types('a->b')[:3], [T.NAME, T.ARROW, T.NAME])
        self.assertEqual(types('a - > b')[:4], [T.NAME, T.MINUS, T.GT, T.NAME])
        self.assertEqual(types('x<=y')[1], T.LE)
        self.assertEqual(types('a==b')[1], T.EQEQ)
        self.assertEqual(types('a!=b')[1], T.NOTEQ)

    def test_bang_alone_L7(self):
        e = err('!x')
        self.assertEqual(e.rule, 'L7')
        self.assertIn('!=', e.message)

    def test_unterminated_string_L6(self):
        e = err('let s = "abc\nprint(s)')
        self.assertEqual((e.rule, e.line, e.col), ('L6', 1, 9))
        e = err('"abc')
        self.assertEqual(e.rule, 'L6')

    def test_hash_inside_string(self):
        toks = tokenize('"a#b"')
        self.assertEqual((toks[0].type, toks[0].value), (T.STRING, 'a#b'))

    def test_comment(self):
        self.assertEqual(types('x # note'), [T.NAME, T.NEWLINE, T.EOF])

    def test_newlines_inside_brackets_D4(self):
        self.assertNotIn(T.NEWLINE, types('f(a,\n b)')[:-2])

    def test_unclosed_bracket_before_a_statement_D4b(self):
        # a line starting with a statement word cannot continue an expression
        self.assertEqual(types('print("a"\nend'), [T.PRINT, T.LPAREN, T.STRING, T.NEWLINE, T.END, T.NEWLINE, T.EOF])
        self.assertEqual(types('f(1,\n  let')[:5], [T.NAME, T.LPAREN, T.NUMBER, T.COMMA, T.NEWLINE])
        # real continuations still join: the next line starts with a value or an operator word
        self.assertNotIn(T.NEWLINE, types('f(1,\n  2)')[:-2])
        self.assertNotIn(T.NEWLINE, types('f(a and\n  not b)')[:-2])
        self.assertNotIn(T.NEWLINE, types('f(a,\n  letter)')[:-2])      # 'letter' is a name, not 'let'

    def test_blank_and_comment_lines_collapse(self):
        self.assertEqual(types('x\n\n\n# c\n\ny'), [T.NAME, T.NEWLINE, T.NAME, T.NEWLINE, T.EOF])

    def test_final_newline_added_L8(self):
        self.assertEqual(types('x'), [T.NAME, T.NEWLINE, T.EOF])
        self.assertEqual(types('x\n'), [T.NAME, T.NEWLINE, T.EOF])

    def test_windows_line_endings(self):
        self.assertEqual(types('x\r\ny\r\n'), types('x\ny\n'))

    def test_degree_sign_L7(self):
        e = err('20°C')
        self.assertEqual(e.rule, 'L7')
        self.assertIn('degC', e.message)

    def test_keywords_and_names_L4(self):
        toks = tokenize('letter Let let _x1')
        self.assertEqual([t.type for t in toks[:4]], [T.NAME, T.NAME, T.LET, T.NAME])

    def test_new_keywords_D19_D20(self):
        self.assertEqual(types('true false and or not')[:5], [T.TRUE, T.FALSE, T.AND, T.OR, T.NOT])

    def test_empty_file(self):
        self.assertEqual(types(''), [T.EOF])
        self.assertEqual(types('\n\n# only a comment\n'), [T.EOF])

    def test_positions_P4(self):
        toks = tokenize('let x = 5 kg\n  print(x)')
        self.assertEqual((toks[0].line, toks[0].col), (1, 1))
        self.assertEqual((toks[4].text, toks[4].col), ('kg', 11))
        p = [t for t in toks if t.type == T.PRINT][0]
        self.assertEqual((p.line, p.col), (2, 3))

    def test_tabs_count_one_column(self):
        toks = tokenize('\tx')
        self.assertEqual(toks[0].col, 2)

    def test_non_ascii_name_L7(self):
        self.assertEqual(err('café = 1').rule, 'L7')
        self.assertIsNone(err('print("café")'))
        self.assertIsNone(err('# café\nx'))

    def test_all_symbols(self):
        src = '+ - * / ^ ( ) , : = < > -> == != <= >='
        expected = [T.PLUS, T.MINUS, T.STAR, T.SLASH, T.CARET, T.LPAREN, T.RPAREN, T.COMMA,
                    T.COLON, T.EQUALS, T.LT, T.GT, T.ARROW, T.EQEQ, T.NOTEQ, T.LE, T.GE]
        self.assertEqual(types(src)[:len(expected)], expected)

    def test_single_quote_L7(self):
        self.assertEqual(err("'a'").rule, 'L7')


if __name__ == '__main__':
    unittest.main()
