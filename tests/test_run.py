"""Phase 4: programs that run (Part 6 output rows, D19-D25), the generator (Part 9)
and the command line and run-time errors (Part 10)."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import TableMixin, compile_full, outcome

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNITS = 'unit m\nunit s\nunit kg\n'


def code_of(src):
    code, errors, _ = compile_full(src)
    assert not errors, errors
    return code


class RunOutputs(TableMixin, unittest.TestCase):
    def test_v1_outputs(self):                                      # Part 6
        self.run_table([
            (UNITS + 'print(5 kg + 3 kg)', '8 kg'),
            (UNITS + 'print(5 kg - 5 kg)', '0 kg'),
            (UNITS + 'print(5 kg / 5 kg)', '1'),
            (UNITS + 'print(2 * 5 kg)', '10 kg'),
            (UNITS + 'print(m)', '1 m'),
            (UNITS + 'print(sqrt(9 m^2))', '3 m'),
            (UNITS + 'print(abs(-3 m))', '3 m'),
            (UNITS + 'print(log(10 m / 1 m))', '2.302585093'),
            ('print(2 ^ 0.5)', '1.414213562'),
            (UNITS + 'let x = 3 m\nx = x + 1 m\nprint(x)', '4 m'),
            (UNITS + 'print(5 m * s)', '5 m * s'),
            (UNITS + 'print(10 kg * m / s^2)', '10 kg * m / s^2'),
            (UNITS + 'print(1 kg / (m * s^2))', '1 kg / (m * s^2)'),
            ('print(f(3))\nfn f(a)\n  return a * 2\nend', '6'),
            ('fn fact(n)\n  if n < 2\n    return 1\n  end\n  return n * fact(n - 1)\nend\nprint(fact(5))', '120'),
            ('fn show(a)\n  print(a)\nend\nshow(7)', '7'),
            ('let i = 0\nwhile i < 3\n  print(i)\n  i = i + 1\nend', '0\n1\n2'),
        ])

    def test_D16_number_format(self):
        self.run_table([
            (UNITS + 'print(0 * -1 m)', '0 m'),
            (UNITS + 'print(1e16 m)', '1e+16 m'),
            ('print(0.1 + 0.2)', '0.3'),
            ('print(20)', '20'),
        ])

    def test_D19_to_D25_outputs(self):
        self.run_table([
            ('print(true)', 'True'),
            ('print(true == false)', 'False'),
            ('let a = 1\nlet b = 2\nprint(a > b)', 'False'),
            ('let a = 1\nlet b = 2\nprint(not a > b)', 'True'),
            ('print(true and false or true)', 'True'),
            (UNITS + 'let a = 5 m\nif a > 0 m and a < 10 m\n  print("in range")\nend', 'in range'),
            ('let x = 2\nif x < 1\n  print(1)\nelse if x < 3\n  print(2)\nelse\n  print(3)\nend', '2'),
            ('let x = 9\nif x < 1\n  print(1)\nelse if x < 3\n  print(2)\nelse\n  print(3)\nend', '3'),
            ('print(pi)', '3.141592654'),
            (UNITS + 'print(2 * pi * 3 m)', '18.84955592 m'),
            (UNITS + 'print("speed:", 3 m / 2 s)', 'speed: 1.5 m / s'),
            ('let a = 1\nlet b = 2\nprint(a, b)', '1 2'),
            ('print("it\'s")', "it's"),
            ('unit INR\nunit USD\nlet rate = 83.2 INR / USD\nprint(20 USD * rate)', '1664 INR'),
        ])

    def test_runtime_errors(self):
        self.run_table([
            (UNITS + 'print(5 m / 0 m)', '!runtime'),
            ('print(sqrt(-4))', '!runtime'),
            ('print((-8) ^ (1 / 3))', '!runtime'),
            ('fn f(n)\n  return f(n + 1)\nend\nprint(f(1))', '!runtime'),
        ])

    def test_long_and_deep_programs(self):
        self.run_table([
            ('print(' + ' + '.join(['1'] * 400) + ')', '400'),
            ('print(' + ' * '.join(['1'] * 300) + ' / 2)', '0.5'),
            ('print(' + '(' * 60 + '1' + ')' * 60 + ')', '1'),
            ('print(' + '(' * 400 + '1' + ')' * 400 + ')', '!P6'),
            ('print(10 - 4 - 3)', '3'),
            ('print(12 / 3 / 2)', '2'),
            ('print(2 * 3 / 4 * 2)', '3'),
            ('print(10 - (4 - 3))', '9'),
        ])

    def test_empty_and_declaration_only(self):
        self.run_table([('', ''), ('unit m\nunit s', '')])


class GeneratorOutput(unittest.TestCase):                           # Part 9
    def test_renaming_D15(self):
        code = code_of('let list = 1\nlet x_ = 2\nlet math = 3\nlet us_print = 4\nprint(list + x_ + math + us_print)')
        for text in ('list_ = 1.0', 'x__ = 2.0', 'math_ = 3.0', 'us_print_ = 4.0'):
            self.assertIn(text, code)
        self.assertEqual(outcome('let list = 1\nlet x_ = 2\nprint(list + x_)'), '3')

    def test_empty_if_body_G4(self):
        code = code_of('if 1 > 0\nend\nprint(1)')
        self.assertIn('if (1.0 > 0.0):\n    pass', code)

    def test_brackets_and_pow_G3_G8(self):
        self.assertIn('(-math.pow(x, 2.0))', code_of('let x = 3\nlet y = -x ^ 2'))
        self.assertIn('y = (a - b - c)', code_of('let a = 1\nlet b = 2\nlet c = 3\nlet y = a - b - c'))

    def test_print_forms_D23(self):
        code = code_of(UNITS + 'let a = 1 m\nprint(a)\nprint("a")\nprint("a:", a, 2)')
        self.assertIn("us_print(a, 'm')", code)
        self.assertIn("us_print('a')", code)
        self.assertIn("us_print('a:', '', a, 'm', 2.0, '')", code)

    def test_hoisted_defs_and_layout_G7(self):
        code = code_of('print(f(1))\nfn f(a)\n  return a\nend')
        lines = code.splitlines()
        self.assertTrue(lines[0].startswith('# Generated by UnitSafe'))
        self.assertEqual(lines[1], 'import math')
        self.assertLess(code.index('def f(a):'), code.index('us_print(f(1.0))'))

    def test_tour_matches_guide(self):
        src = (ROOT / 'tests/programs/sample01_tour.us').read_text()
        code = code_of(src)
        for text in ('def stop_distance(v, a):', '    return (math.pow(v, 2.0) / (2.0 * a))',
                     'speed = (20.0 / 1.0)', 'decel = (5.0 / math.pow(1.0, 2.0))',
                     "if (d > 30.0):\n    us_print('too far')\nelse:\n    us_print(d, 'm')"):
            self.assertIn(text, code)

    def test_elif_D21(self):
        code = code_of('let x = 1\nif x < 1\n  print(1)\nelse if x < 2\n  print(2)\nend')
        self.assertIn('elif (x < 2.0):', code)

    def test_logic_and_bools(self):
        code = code_of('let a = true\nlet b = not a and false')
        self.assertIn('b = ((not a) and False)', code)

    def test_number_too_large_never_reaches_generator(self):
        self.assertEqual(outcome('print(1e400)')[:3], '!L5')


def cli(*args, stdin_text=None):
    p = subprocess.run([sys.executable, '-m', 'unitsafe', *args], cwd=ROOT,
                       capture_output=True, text=True, timeout=30)
    return p.returncode, p.stdout, p.stderr


class CommandLine(unittest.TestCase):                                # Part 10
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.write_text(text, encoding='utf-8')
        return str(p)

    def test_run_ok(self):
        code, out, err = cli('run', self.write('a.us', UNITS + 'print(2 m)'))
        self.assertEqual((code, out.strip(), err), (0, '2 m', ''))

    def test_empty_file(self):
        self.assertEqual(cli('run', self.write('e.us', ''))[:2], (0, ''))

    def test_compile_error_format(self):
        code, out, err = cli('run', self.write('braking.us', UNITS + 'let y = 1\nlet x = 5 kg + 3 m'))
        self.assertEqual(code, 1)
        self.assertEqual(err.strip().splitlines(), [
            'braking.us:5:14: error [U6]: cannot add kg and m',
            '    let x = 5 kg + 3 m',
            '                 ^',
            '1 error'])

    def test_three_errors_sorted(self):
        src = UNITS + 'print(1 m + 1 s)\nprint(1 kg + 1 s)\nprint(2 m + 1)'
        code, out, err = cli('check', self.write('t.us', src))
        self.assertEqual(code, 1)
        self.assertTrue(err.strip().endswith('3 errors'))
        self.assertLess(err.index(':4:'), err.index(':5:'))

    def test_lexer_error_stops_pipeline(self):
        code, out, err = cli('check', self.write('l.us', UNITS + 'print(1 m + 1 s)\nlet a = @'))
        self.assertEqual(code, 1)
        self.assertIn('[L7]', err)
        self.assertNotIn('[U6]', err)

    def test_check_ok(self):
        self.assertEqual(cli('check', self.write('c.us', 'print(1)'))[:2], (0, 'ok: no errors\n'))

    def test_build_writes_file(self):
        src = self.write('b.us', 'print(1)')
        code, out, err = cli('build', src)
        self.assertEqual(code, 0)
        py = self.dir / 'b.py'
        self.assertTrue(py.exists())
        r = subprocess.run([sys.executable, str(py)], capture_output=True, text=True)   # D14: standalone
        self.assertEqual(r.stdout, '1\n')
        code, out, err = cli('build', src, '-o', str(self.dir / 'other.py'))
        self.assertTrue((self.dir / 'other.py').exists())
        cli('build', src)                                             # overwrites without complaint
        self.assertEqual(code, 0)

    def test_build_with_errors_writes_nothing(self):
        src = self.write('bad.us', UNITS + 'print(1 m + 1 s)')
        code, out, err = cli('build', src)
        self.assertEqual(code, 1)
        self.assertFalse((self.dir / 'bad.py').exists())               # G6

    def test_runtime_error_maps_line(self):
        code, out, err = cli('run', self.write('z.us', UNITS + 'print(1)\nprint(5 m / 0 m)'))
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), 'runtime error at line 5: division by zero')
        code, out, err = cli('run', self.write('q.us', 'print(sqrt(-4))'))
        self.assertEqual((code, err.strip()), (2, 'runtime error at line 1: math domain error'))
        for src, msg in (('print(log(0))', 'math domain error'),
                         ('print((-8) ^ (1 / 3))', 'math domain error'),
                         ('print(10 ^ 400)', 'math range error')):
            code, out, err = cli('run', self.write('m.us', src))
            self.assertEqual((code, err.strip()), (2, 'runtime error at line 1: ' + msg))

    def test_infinite_recursion(self):
        code, out, err = cli('run', self.write('r.us', 'fn f(n)\n  return f(n + 1)\nend\nprint(f(1))'))
        self.assertEqual(code, 2)
        self.assertIn('maximum recursion depth exceeded', err)

    def test_usage_and_missing_file(self):
        self.assertEqual(cli()[0], 3)
        self.assertEqual(cli('fly', 'x.us')[0], 3)
        self.assertEqual(cli('run', str(self.dir / 'missing.us'))[0], 3)
        bad = self.dir / 'latin.us'
        bad.write_bytes(b'print("\xe9")')
        self.assertEqual(cli('run', str(bad))[0], 3)

    def test_debug_commands(self):
        code, out, err = cli('tokens', self.write('k.us', 'let x = 5 kg'))
        self.assertEqual(code, 0)
        self.assertIn('NUMBER', out)
        code, out, err = cli('ast', self.write('k2.us', 'let x = 5 kg'))
        self.assertIn('UnitLiteral', out)


if __name__ == '__main__':
    unittest.main()
    