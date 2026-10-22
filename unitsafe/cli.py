"""Command line (build guide Part 10): run, build, check, tokens, ast.

Exit codes: 0 ok, 1 compile errors, 2 run-time error, 3 usage or file problem.
"""
import os
import sys

from .ast_nodes import dump
from .checker import Checker
from .codegen import Generator
from .errors import CompileError, LexError, ParseError, format_errors
from .lexer import Lexer
from .parser import Parser

USAGE = 'usage: python -m unitsafe {run|build|check|tokens|ast} FILE.us [-o OUT.py]'
RUNTIME_ERRORS = (ZeroDivisionError, ValueError, OverflowError, RecursionError)
RUNTIME_MESSAGES = {
    ZeroDivisionError: 'division by zero',
    ValueError: 'math domain error',               # e.g. sqrt(-4), log(0), (-8) ^ (1 / 3)
    OverflowError: 'math range error',             # e.g. 10 ^ 400
    RecursionError: 'maximum recursion depth exceeded',
}


TOO_DEEP = CompileError('P6', 1, 1, 'the program is nested too deeply; split long expressions into smaller lets')


def compile_full(text: str, filename: str = 'program.us'):
    """(python code or None, errors, line map). Never raises for a bad program."""
    if sys.getrecursionlimit() < 4000:
        sys.setrecursionlimit(4000)                    # room for long but reasonable expressions
    try:
        try:
            tokens = Lexer(text).run()
            tree = Parser(tokens).parse()
        except (LexError, ParseError) as e:
            return None, [e.error], {}                 # one error, stop
        errors = Checker().run(tree)
        if errors:
            return None, errors, {}                    # all checker errors, no code (G6)
        gen = Generator()
        code = gen.run(tree, filename)
        compile(code, '<unitsafe>', 'exec')            # Python has its own nesting limits
    except (RecursionError, SyntaxError, MemoryError):
        return None, [TOO_DEEP], {}
    return code, [], gen.line_map


def compile_source(text: str, filename: str = 'program.us'):
    code, errors, _ = compile_full(text, filename)
    return code, errors


def runtime_line(exc, line_map):
    """The UnitSafe line of the last generated-code frame in the traceback."""
    tb, line = exc.__traceback__, None
    while tb is not None:                      # skip frames inside the print helper
        if tb.tb_frame.f_code.co_filename == '<unitsafe>' and tb.tb_lineno in line_map:
            line = line_map[tb.tb_lineno]
        tb = tb.tb_next
    return line


def run_code(code: str, line_map: dict) -> int:
    try:
        exec(compile(code, '<unitsafe>', 'exec'), {'__name__': '__main__'})
    except RUNTIME_ERRORS as e:
        line = runtime_line(e, line_map)
        where = f' at line {line}' if line else ''
        msg = next(m for t, m in RUNTIME_MESSAGES.items() if isinstance(e, t))   # fixed text on every Python version
        print(f'runtime error{where}: {msg}', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


def main(argv) -> int:
    commands = ('run', 'build', 'check', 'tokens', 'ast')
    if len(argv) < 2 or argv[0] not in commands:
        print(USAGE, file=sys.stderr)
        return 3
    cmd, path = argv[0], argv[1]
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f'cannot read {path}: {e}', file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 3
    filename = os.path.basename(path)

    if cmd in ('tokens', 'ast'):
        try:
            tokens = Lexer(text).run()
            if cmd == 'tokens':
                for t in tokens:
                    print(f'{t.line}:{t.col}\t{t.type.name}\t{t.text!r}')
            else:
                print(dump(Parser(tokens).parse()))
        except (LexError, ParseError) as e:
            print(format_errors([e.error], filename, text), file=sys.stderr)
            return 1
        return 0

    code, errors, line_map = compile_full(text, filename)
    if errors:
        print(format_errors(errors, filename, text), file=sys.stderr)
        return 1
    if cmd == 'check':
        print('ok: no errors')
        return 0
    if cmd == 'build':
        out = os.path.splitext(path)[0] + '.py'
        if '-o' in argv:
            i = argv.index('-o')
            if i + 1 >= len(argv):
                print(USAGE, file=sys.stderr)
                return 3
            out = argv[i + 1]
        with open(out, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f'wrote {out}')
        return 0
    try:
        return run_code(code, line_map)
    except KeyboardInterrupt:
        return 130