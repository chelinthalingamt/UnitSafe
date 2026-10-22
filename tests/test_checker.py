"""Phase 3: build guide Parts 5 and 6 edge cases (and the D19-D25 rows), checked
without running the program: 'ok' means no errors, '!RULE' the expected errors."""
import unittest

from tests.helpers import matches
from unitsafe.checker import Checker
from unitsafe.errors import LexError, ParseError
from unitsafe.lexer import tokenize
from unitsafe.parser import parse

UNITS = 'unit m\nunit s\nunit kg\n'


def check_src(src):
    try:
        prog = parse(tokenize(src))
    except (LexError, ParseError) as e:
        return f'!{e.error.rule}@{e.error.line}'
    errs = Checker().run(prog)
    return '!' + ' '.join(f'{e.rule}@{e.line}' for e in errs) if errs else 'ok'


def messages(src):
    return [e.message for e in Checker().run(parse(tokenize(src)))]


class TableTest(unittest.TestCase):
    def run_rows(self, rows):
        for src, expected in rows:
            with self.subTest(src=src):
                got = check_src(src)
                self.assertTrue(matches(got, expected), f'\n{src}\nexpected {expected!r}, got {got!r}')


class SymbolTableEdgeCases(TableTest):                  # Part 5
    def test_rows(self):
        self.run_rows([
            ('unit m\nlet m = 5', '!U2'),
            ('let x = 1\nunit x', '!U2'),
            ('let sqrt = 2', '!S2c'),
            ('let pi = 3', '!S2c'),
            ('let x = 1\nlet x = 2', '!S2@2'),
            (UNITS + 'let x = 1 m\nif x > 0 m\n  let x = 2 s\nend', '!D7@6'),
            (UNITS + 'if 1 > 0\n  let t = 1 s\nend\nif 2 > 0\n  let t = 2 s\nend', 'ok'),
            ('let x = 1\nfn f()\n  let x = 2\n  return x\nend', 'ok'),
            ('let x = 1\nfn f()\n  return x\nend', '!D8@3'),
            ('let x = 1\nfn f()\n  x = 2\nend', '!D8@3'),
            ('fn f(M)\n  return M\nend\nfn g(M)\n  return M\nend', 'ok'),
            ('fn f(f)\n  return 1\nend', '!S2'),
            ('fn g(a, a)\n  return a\nend', '!S2'),
            ('fn f()\n  unit kg\n  return 1\nend', '!S11'),
            ('if 1 > 0\n  unit kg\nend', '!S11'),
            ('if 1 > 0\n  fn f()\n    return 1\n  end\nend', '!S11'),
            ('print(f(2))\nfn f(a)\n  return a * 2\nend', 'ok'),
            ('fn fact(n)\n  if n < 2\n    return 1\n  end\n  return n * fact(n - 1)\nend', 'ok'),
            ('let x = x + 1', '!S1'),
            ('unit m\nfn f(v: kmh) -> m\n  return 1 m\nend\nunit kmh', '!U1@2'),
            ('kind torque', 'ok'),
        ])


class CheckerV1EdgeCases(TableTest):                     # Part 6
    def test_rows(self):
        self.run_rows([
            (UNITS + 'print(5 kg + 3 kg)', 'ok'),
            (UNITS + 'print(5 kg + 3 m)', '!U6@4'),
            (UNITS + 'print(5 kg + 2)', '!U6'),
            (UNITS + 'print(0 + 5 m)', '!U6'),
            (UNITS + 'print(5 kg - 5 kg)', 'ok'),
            (UNITS + 'print(5 kg / 5 kg)', 'ok'),
            (UNITS + 'print(2 * 5 kg)', 'ok'),
            (UNITS + 'print(m)', 'ok'),
            (UNITS + 'let x = 3 m\nx = 5 s', '!U8@5'),
            (UNITS + 'let x = 3 m\nx = "hi"', '!S7'),
            (UNITS + 'let x: m = 5', '!U8'),
            (UNITS + 'fn speed(d: m, t: s) -> m / s\n  return d / t\nend\nprint(speed(10 s, 100 m))',
             '!U9@7 U9@7'),
            (UNITS + 'fn f(d: m) -> m / s\n  return d\nend', '!U9@5'),
            (UNITS + 'fn f(d: m) -> m\n  if d > 1 m\n    return d\n  end\nend', '!S8@4'),
            (UNITS + 'fn f()\n  return 5 m\nend', '!U9@5'),
            ('fn log_it(a)\n  print(a)\nend\nlet y = log_it(3)', '!S9@4'),
            ('fn log_it(a)\n  print(a)\nend\nlog_it(3)', 'ok'),
            ('return 5', '!S5'),
            (UNITS + 'print(5 kgg)', '!U1'),
            (UNITS + 'let x = 1\nprint(2 x)', '!U1'),
            (UNITS + 'let n = 2\nlet a = 3 m ^ n', '!U10'),
            (UNITS + 'let x = 3 m\nlet a = x ^ 2.0', '!U10'),
            ('print(2 ^ 0.5)', 'ok'),
            (UNITS + 'print(2 ^ (3 m))', '!U10'),
            (UNITS + 'print(sqrt(9 m^2))', 'ok'),
            (UNITS + 'print(sqrt(9 m))', '!U11'),
            (UNITS + 'print(sin(3 m))', '!A3'),                  # A3 replaced U11 for trig in phase 7
            (UNITS + 'print(exp(1 s))', '!U11'),
            (UNITS + 'print(log(10 m / 1 m))', 'ok'),
            (UNITS + 'print(abs(-3 m))', 'ok'),
            (UNITS + 'print(atan2(1 m, 1 s))', '!A4'),
            (UNITS + 'if 5 m > 2 s\n  print(1)\nend', '!U6@4'),
            (UNITS + 'if 5 m\n  print(1)\nend', '!S6'),
            ('let a = 1\nlet b = 2\nlet ok = a > b\nwhile ok\n  ok = a < b\nend', 'ok'),
            ('print("a" + "b")', '!S3'),
            ('print("a" == "b")', 'ok'),
            ('print("a" < "b")', '!S3'),
            ('let a = 1\nlet b = 2\nprint((a > b) + 1)', '!S3'),
            ('fn f()\n  return 1\nend\nprint(f)', '!S12'),
            ('let x = 1\nprint(x(3))', '!S12'),
            (UNITS + 'let x = 5 kg + 3 s\nprint(x + 1 kg)', '!U6@4'),
            (UNITS + 'print(5 m / 0 m)', 'ok'),
            ('print(sqrt(-4))', 'ok'),
            ('print(f(1))', '!S1'),
            ('print(sqrt(1, 2))', '!S4'),
            ('fn f(a)\n  return a\nend\nprint(f(1, 2))', '!S4'),
            (UNITS + 'let x = -(5 m) + 1 m', 'ok'),
            (UNITS + 'let x = 5 m * s', 'ok'),
            (UNITS + 'let x = 3 m\nx = x + 1 m', 'ok'),
        ])

    def test_message_wording(self):
        self.assertEqual(messages(UNITS + 'print(5 kg + 3 m)'), ['cannot add kg and m'])
        self.assertEqual(messages(UNITS + 'print(5 kg + 2)'), ['cannot add kg and no unit'])
        self.assertEqual(messages(UNITS + 'let x = 1\nprint(2 x)'), ["'x' is a variable, not a unit; write 2 * x"])
        self.assertEqual(messages(UNITS + 'if 5 m > 2 s\n  print(1)\nend'), ['cannot compare m and s in this condition'])
        self.assertEqual(messages(UNITS + 'let x = 3 m\nlet a = x ^ 2.0'),
                         ['the power of a value with a unit must be a whole-number literal; write 2'])
        self.assertEqual(messages(UNITS + 'print(sqrt(9 m))'), ['sqrt of m has an odd power'])
        self.assertEqual(messages('let x = 1\nfn f()\n  return x\nend'),
                         ["functions cannot use the global variable 'x'; pass it in as a parameter"])


class CheckerD19toD25(TableTest):
    def test_rows(self):
        self.run_rows([
            ('print(true)', 'ok'),
            ('let ok = true\nok = 5', '!S7'),
            ('print(true + 1)', '!S3'),
            (UNITS + 'let a = 5 m\nif a > 0 m and a < 10 m\n  print(a)\nend', 'ok'),
            (UNITS + 'let a = 5 m\nif a > 0 m and 5\n  print(a)\nend', '!S3'),
            (UNITS + 'let x = 2\nif 5 m > 2 s or x > 1\n  print(x)\nend', '!U6'),
            ('let a = 1\nlet b = 2\nprint(not a > b)', 'ok'),
            (UNITS + 'print(not 5 m)', '!S3'),
            ('print(true == false)', 'ok'),
            ('print(true < false)', '!S3'),
            ('if true\n  print(1)\nelse if false\n  print(2)\nelse\n  print(3)\nend', 'ok'),
            (UNITS + 'print(2 * pi * 3 m)', 'ok'),
            ('fn log_it(a)\n  print(a)\nend\nprint(log_it(1), 2)', '!S10'),
            ('unit INR\nunit USD\nlet rate = 83.2 INR / USD\nprint(20 USD * rate)', 'ok'),
            ('unit INR\nunit USD\nprint(20 USD + 1664 INR)', '!U6'),
            ('unit INR\nunit USD\nlet rate = 83.2 INR / USD\nlet inr: INR = 20 USD / rate', '!U8@4'),
        ])


if __name__ == '__main__':
    unittest.main()
