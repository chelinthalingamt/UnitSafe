"""Phase 2: every row of build guide Part 3 'Edge cases', plus D19-D23."""
import unittest

from unitsafe import ast_nodes as A
from unitsafe.errors import ParseError
from unitsafe.lexer import tokenize
from unitsafe.parser import parse


def mk(cls, **kw):
    return cls(line=0, col=0, **kw)


def num(v):
    return mk(A.Number, value=float(v), text=str(v))


def name(n):
    return mk(A.Name, name=n)


def lit(v, unit, power=1, delta=False):
    return mk(A.UnitLiteral, value=float(v), text=str(v), unit=unit, power=power, delta=delta)


def expr(src):
    """Parse 'let _ = <src>' and return the value expression."""
    return parse(tokenize('let _ = ' + src)).body[0].value


def stmts(src):
    return parse(tokenize(src)).body


def perr(src):
    try:
        parse(tokenize(src))
    except ParseError as e:
        return e.error
    return None


class ParserEdgeCases(unittest.TestCase):
    def test_unit_literal_binds_tightest_U3(self):
        self.assertEqual(expr('a / 2 s'), mk(A.BinOp, op='/', left=name('a'), right=lit(2, 's')))

    def test_power_belongs_to_unit_D1(self):
        self.assertEqual(expr('5 m^2'), lit(5, 'm', 2))
        self.assertEqual(expr('5 s^-2'), lit(5, 's', -2))

    def test_bracketed_literal_power(self):
        self.assertEqual(expr('(5 m) ^ 2'), mk(A.Power, base=lit(5, 'm'), exp=num(2)))

    def test_variable_power_left_for_checker(self):
        self.assertEqual(expr('5 m ^ x'), mk(A.Power, base=lit(5, 'm'), exp=name('x')))
        self.assertEqual(expr('5 m^2.5'), mk(A.Power, base=lit(5, 'm'), exp=num(2.5)))

    def test_lone_unit_name_D17(self):
        e = expr('9.8 m / s^2')
        self.assertEqual(e, mk(A.BinOp, op='/', left=lit(9.8, 'm'),
                               right=mk(A.Power, base=name('s'), exp=num(2))))

    def test_number_then_variable_is_literal(self):
        self.assertEqual(expr('2 x'), lit(2, 'x'))

    def test_two_units_need_operator(self):
        e = perr('let a = 5 m s')
        self.assertEqual(e.rule, 'P6')
        self.assertIn("expected end of line, found 's'", e.message)

    def test_unary_minus_D2(self):
        self.assertEqual(expr('-x ^ 2'), mk(A.Neg, operand=mk(A.Power, base=name('x'), exp=num(2))))
        self.assertEqual(expr('-5 m'), mk(A.Neg, operand=lit(5, 'm')))

    def test_negative_exponent_D3(self):
        self.assertEqual(expr('2 ^ -1'), mk(A.Power, base=num(2), exp=mk(A.Neg, operand=num(1))))

    def test_repeated_power_D3(self):
        self.assertIn('brackets', perr('let a = 2 ^ 3 ^ 2').message)

    def test_one_comparison(self):
        self.assertIn('only one comparison', perr('let a = a < b < c').message)

    def test_print_errors(self):
        self.assertIn("expected a value, found ')'", perr('print()').message)
        self.assertIn("expected a value, found ')'", perr('print("x", )').message)
        self.assertIn("'in' is only allowed", perr('print((d in km))').message)
        self.assertIn("'in' is only allowed", perr('let x = d in km').message)

    def test_print_several_values_D23(self):
        p = stmts('print(a, b)')[0]
        self.assertEqual(len(p.args), 2)
        p = stmts('print("speed:", v in km / h, t in min)')[0]
        self.assertEqual([a.target is not None for a in p.args], [False, True, True])
        self.assertEqual(p.args[1].target.expr,
                         mk(A.UnitDiv, left=mk(A.UnitName, name='km'), right=mk(A.UnitName, name='h')))

    def test_only_one_in_units(self):
        self.assertIn('only the number 1', perr('let x: 1000 m = 5 km').message)

    def test_unit_power_zero(self):
        self.assertIn('power of 0', perr('let a = 5 m^0').message)
        self.assertIn('power of 0', perr('let a: m^0 = 1').message)

    def test_unit_decl_forms(self):
        self.assertEqual(stmts('unit km = 1000 m')[0],
                         mk(A.UnitDecl, name='km', number=1000.0, expr=mk(A.UnitName, name='m')))
        self.assertEqual(stmts('unit Hz = 1 / s')[0],
                         mk(A.UnitDecl, name='Hz', expr=mk(A.UnitDiv, left=mk(A.UnitOne),
                                                           right=mk(A.UnitName, name='s'))))
        self.assertIn('kHz = 1000', perr('unit kHz = 1000 / s').message)
        d = stmts('unit degC = 1 K offset 273.15')[0]
        self.assertEqual((d.number, d.offset), (1.0, 273.15))
        d = stmts('unit J = N * m of energy')[0]
        self.assertEqual(d.kind, 'energy')
        d = stmts('unit L = 0.001 m^3')[0]
        self.assertEqual(d.expr, mk(A.UnitPow, base=mk(A.UnitName, name='m'), exp=3))
        d = stmts('unit A2 = (m / s)^2')[0]
        self.assertIsInstance(d.expr, A.UnitPow)

    def test_missing_end(self):
        e = perr('if x > 1\n  print(x)\n')
        self.assertIn("expected 'end' to close the 'if' on line 1", e.message)
        e = perr('while x > 1\n  print(x)')
        self.assertIn("'while' on line 1", e.message)

    def test_else_if_chain_D21(self):
        s = stmts('if a\n print(1)\nelse if b\n print(2)\nelse\n print(3)\nend')[0]
        self.assertIsInstance(s.els[0], A.If)
        self.assertTrue(s.els[0].elif_chain)
        self.assertEqual(len(s.els[0].els), 1)
        e = perr('if a\n print(1)\nelse if b\n print(2)\n')
        self.assertIn("'end' to close the 'if' on line 1", e.message)

    def test_missing_value(self):
        self.assertIn('found end of line', perr('x =\nprint(1)').message)
        self.assertIn("expected a value, found ')'", perr('f(1,)').message)
        self.assertIn("expected a parameter name, found ')'", perr('fn f(a,)\nend').message)

    def test_bad_statement_starts(self):
        self.assertIn("expected '=' or '(' after x", perr('x 5').message)
        self.assertIn("expected a name after let, found '5'", perr('let 5 = x').message)
        self.assertIn("expected a statement, found ')'", perr(')').message)
        self.assertIn("expected a statement, found 'end'", perr('end').message)
        self.assertIn("expected 'fn' after 'empirical'", perr('empirical let').message)

    def test_call_statement_D6(self):
        s = stmts('show(3)')[0]
        self.assertIsInstance(s, A.CallStmt)
        self.assertEqual(s.call.args, [num(3)])

    def test_logic_precedence_D20(self):
        self.assertEqual(expr('not a > b'),
                         mk(A.Not, operand=mk(A.Compare, op='>', left=name('a'), right=name('b'))))
        e = expr('a and b or c')
        self.assertEqual(e, mk(A.Logic, op='or', left=mk(A.Logic, op='and', left=name('a'), right=name('b')),
                               right=name('c')))
        e = expr('a < b and b < c')
        self.assertEqual(e.op, 'and')

    def test_bools_D19(self):
        self.assertEqual(expr('true'), mk(A.Bool, value=True))
        self.assertEqual(expr('false'), mk(A.Bool, value=False))

    def test_annotations(self):
        s = stmts('let tau: N * m of torque = 40 N * m')[0]
        self.assertEqual(s.ann.kind, 'torque')
        s = stmts('let d: delta degC = 5 delta degC')[0]
        self.assertTrue(s.ann.delta)
        self.assertEqual(s.value, lit(5, 'degC', delta=True))

    def test_function_forms(self):
        f = stmts('empirical fn m(mass: kg) -> W\n return mass\nend')[0]
        self.assertTrue(f.empirical)
        self.assertEqual([p.name for p in f.params], ['mass'])
        self.assertIsNotNone(f.ret)

    def test_operator_positions(self):
        s = stmts('let x = 5 kg + 3 m')[0]
        self.assertEqual((s.value.line, s.value.col), (1, 14))   # the '+'

    def test_newlines_in_brackets_D4(self):
        e = stmts('let a = (1 +\n 2)')[0].value
        self.assertEqual(e, mk(A.BinOp, op='+', left=num(1), right=num(2)))



def perrs(src):
    try:
        parse(tokenize(src))
    except ParseError as e:
        return [err.line for err in e.errors]
    return []


class SeveralSyntaxErrorsD26(unittest.TestCase):
    def test_independent_errors(self):
        self.assertEqual(perrs('let = 1\nprint(1)\nlet y =\nprint(2)'), [1, 3])
        self.assertEqual(perrs('end\nend\nprint(1)'), [1, 2])

    def test_error_inside_a_block_keeps_the_block(self):
        self.assertEqual(perrs('if x > 1\n  let = 5\n  print(x)\nend\nlet y =\n'), [2, 5])
        self.assertEqual(perrs('while x < 3\n  x = \n  print(x)\nend'), [2])

    def test_error_in_a_block_header_reads_the_block(self):
        self.assertEqual(perrs('if x >\n  print(1)\nend\nlet a = 2 2'), [1, 4])
        self.assertEqual(perrs('if a\n  print(1)\nelse if b >\n  print(2)\nend\nlet = 1'), [3, 6])
        self.assertEqual(perrs('fn f(a,)\n  return a\nend\nprint(1)'), [1])
        self.assertEqual(perrs('if a\n  if b >\n    print(1)\n  end\nend\nprint(2)'), [2])

    def test_missing_end_is_one_error(self):
        self.assertEqual(perrs('if a\n  print(1)\n'), [3])
        self.assertEqual(len(perrs('if a\n  while b\n    print(1)\n  end\n')), 1)

    def test_stops_after_20(self):
        self.assertEqual(perrs('\n'.join(['let = 1'] * 25)), list(range(1, 21)))

    def test_valid_program_has_no_errors(self):
        self.assertEqual(perrs('if a\n  print(1)\nelse if b\n  print(2)\nelse\n  print(3)\nend'), [])

if __name__ == '__main__':
    unittest.main()
