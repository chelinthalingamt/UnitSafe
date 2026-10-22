"""Shared helpers for the tests. Standard library only (unittest)."""
import contextlib
import io
import re

PROGRAM_EXCEPTIONS = (ZeroDivisionError, ValueError, OverflowError, RecursionError)


def current_phase() -> int:
    try:
        from unitsafe import checker
        return getattr(checker, 'PHASE', 99)
    except ImportError:
        return 0


def compile_full(src: str):
    from unitsafe.cli import compile_full as cf
    return cf(src, 'test.us')


def outcome(src: str) -> str:
    """Run a UnitSafe program and describe what happened.

    Output lines joined by newlines, or '!RULE RULE ...' for compile errors
    (each with '@line'), or '!runtime' for a run-time error.
    """
    code, errors, _ = compile_full(src)
    if errors:
        return '!' + ' '.join(f'{e.rule}@{e.line}' for e in errors)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, '<unitsafe>', 'exec'), {'__name__': '__main__'})
    except PROGRAM_EXCEPTIONS:
        return '!runtime'
    return buf.getvalue().rstrip('\n')


def matches(got: str, expected: str) -> bool:
    """expected '!U6' matches '!U6@3'; expected '!U6@3' must match the line too."""
    if expected.startswith('!') and got.startswith('!'):
        want = expected[1:].split()
        have = got[1:].split()
        if len(want) != len(have):
            return False
        for w, h in zip(want, have):
            if '@' in w:
                if w != h:
                    return False
            elif w != h.split('@')[0]:
                return False
        return True
    return got == expected


class TableMixin:
    """Run a list of (source, expected) rows as subtests."""

    def run_table(self, rows):
        for src, expected in rows:
            with self.subTest(src=src):
                got = outcome(src)
                self.assertTrue(matches(got, expected), f'\nsource:\n{src}\nexpected: {expected!r}\ngot:      {got!r}')
