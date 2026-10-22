"""Every .us file in tests/programs with its .expected file (build guide Part 11).

  name.us         -> .expected holds the exact printed lines
  name_fail.us    -> .expected holds 'RULE LINE' per error, e.g. 'U6 7'
  name_runtime.us -> .expected holds 'runtime LINE'
A file starting with '# phase: N' is skipped until the checker reaches phase N.
"""
import contextlib
import io
import pathlib
import re
import unittest

from tests.helpers import PROGRAM_EXCEPTIONS, current_phase

PROGRAMS = pathlib.Path(__file__).parent / 'programs'


def needed_phase(text: str) -> int:
    m = re.match(r'#\s*phase:\s*(\d+)', text)
    return int(m.group(1)) if m else 4


class ProgramTests(unittest.TestCase):
    pass


def _make(path):
    def test(self):
        text = path.read_text(encoding='utf-8')
        if current_phase() < needed_phase(text):
            self.skipTest(f'needs phase {needed_phase(text)}')
        from unitsafe.cli import compile_full
        expected = path.with_suffix('.expected').read_text(encoding='utf-8').splitlines()
        code, errors, line_map = compile_full(text, path.name)
        if '_fail' in path.stem:
            self.assertEqual([f'{e.rule} {e.line}' for e in errors], expected)
            return
        self.assertEqual(errors, [], [e.message for e in errors])
        compiled = compile(code, '<unitsafe>', 'exec')          # the output is valid Python
        buf = io.StringIO()
        if '_runtime' in path.stem:
            from unitsafe.cli import runtime_line
            with self.assertRaises(PROGRAM_EXCEPTIONS) as ctx, contextlib.redirect_stdout(buf):
                exec(compiled, {'__name__': '__main__'})
            self.assertEqual([f'runtime {runtime_line(ctx.exception, line_map)}'], expected)
            return
        with contextlib.redirect_stdout(buf):
            exec(compiled, {'__name__': '__main__'})
        self.assertEqual(buf.getvalue().splitlines(), expected)
    return test


for _p in sorted(PROGRAMS.glob('*.us')):
    setattr(ProgramTests, 'test_' + _p.stem, _make(_p))

if __name__ == '__main__':
    unittest.main()
