"""Error records, message templates and formatting (build guide Parts 2, 10 and the error catalogue)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CompileError:
    rule: str        # 'L7', 'P6', 'U6', ...
    line: int
    col: int
    message: str


class LexError(Exception):
    """Carries one CompileError; stops the pipeline."""
    def __init__(self, error: CompileError):
        super().__init__(error.message)
        self.error = error


class ParseError(Exception):
    """Carries the first CompileError, and all of them in .errors (D26: up to 20)."""
    def __init__(self, error: CompileError, errors=None):
        super().__init__(error.message)
        self.error = error
        self.errors = errors or [error]


# One place for every checker message (error catalogue). Keys are rule IDs,
# with a suffix when a rule has more than one message.
MESSAGES = {
    'S1': "'{name}' is not declared",
    'S2': "'{name}' is already declared on line {n}",
    'S2.fn': "'{name}' is a function name",
    'S2c': "'{name}' is a built-in name",
    'S3': "cannot {verb} {type} values",
    'S3.order': "can only order numbers",
    'S3.mixed': "cannot compare a {a} with a {b}",
    'S3.logic': "{op} needs bools, got a {type}",
    'S3.fnarg': "{f} needs a number, got a {type}",
    'S4': "'{f}' takes {n} arguments, got {m}",
    'S5': "return is only allowed inside a function",
    'S6': "the condition must be a comparison or a bool, got a {type}",
    'S7': "{what} holds a {t}, not a {v}",
    'S8b': "'{f}' promises a result but does not end with return",
    'S9': "'{f}' gives no value",
    'S10': "'{f}' gives no value to print",
    'S11': "{what} declarations are only allowed at the top level",
    'S12.value': "'{name}' is a {cat}; call it with ( )",
    'S12.kind': "'{name}' is a kind, not a value",
    'S12.notfn': "'{name}' is not a function",
    'S12.notvar': "'{name}' is a {cat}, not a variable",
    'D7': "'{name}' is already declared on line {n} in an enclosing block; choose another name",
    'D8': "functions cannot use the global variable '{name}'; pass it in as a parameter",
    'D13': "kelvin needs a temperature reading",
    'U1': "'{u}' is not a declared unit",
    'U1.var': "'{u}' is a variable, not a unit; write {n} * {u}",
    'U2': "'{name}' is a unit name",
    'U2.var': "'{name}' is already a variable",
    'U6': "cannot {verb} {a} and {b}{where}",
    'U8': "{what} holds {a}, cannot store {b}",
    'U9.arg': "argument '{p}' holds {a}, cannot store {b}",
    'U9.ret': "'{f}' promises {a}, cannot return {b}",
    'U9.noresult': "'{f}' declares no unit for its result; this returns {b}",
    'U10': "the power of a value with a unit must be a whole-number literal",
    'U10.hint': "the power of a value with a unit must be a whole-number literal; write {n}",
    'U10b': "the power itself must have no unit, got {a}",
    'U11.nounit': "{f} needs a value with no unit, got {a}",
    'U11.odd': "sqrt of {a} has an odd power",
    'U11.atan2': "atan2 needs two values with the same unit, got {a} and {b}",
    'C1': "'{u}' is not a declared unit",
    'C3': "'{u}' is already declared",
    'C3.builtin': "'{u}' is built in",
    'C3.factor': "a conversion factor must be above 0",
    'C6': "cannot convert {a} to {b}",
    'A3': "{f} needs an angle (rad) but got {a}; write 90 deg or 90 rad",
    'A3.plain': "{f} needs an angle but got a plain number; write {n} deg or {n} rad",
    'A3.plainvar': "{f} needs an angle but got a plain number; multiply it by deg or rad",
    'A3.pi': "{f} needs an angle but got a plain number; write pi * rad",
    'A4': "{f} needs a value with no unit, got {a}",
    'K1': "'{k}' is not a declared kind",
    'K2': "'{u}' already has the kind {k}",
    'K3': "cannot {verb} {k1} and {k2}",
    'K3.plain': "cannot {verb} {k} and a plain value; write of {k} to label it",
    'K5': "{what} holds {k1}, not {k2}",
    'K5.plain': "{what} is plain and cannot hold {k}",
    'K6': "'{k}' is already declared",
    'T1': "an offset unit must be based on a single unit with no offset",
    'T2': "delta only applies to units with an offset",
    'T3.add': "cannot add two temperature readings",
    'T3.sub': "cannot subtract a reading from a change",
    'T3.op': "cannot {op} a reading; convert first with kelvin(...)",
    'T3.cmp': "cannot compare a reading with a change",
    'T5': "{u} has an offset and cannot be part of a compound unit or a power",
    'T5b': "{u} alone is not a value; write 1 {u} or 1 delta {u}",
    'T6.change': "{what} is a change; write delta {u}",
    'T6.reading': "{what} is a reading; leave out delta",
    'T8.reading': "{what} holds a reading, cannot store a change",
    'T8.change': "{what} holds a change, cannot store a reading; use kelvin(...) or declare it with a reading unit such as degC",
    'E1.param': "parameter '{p}' needs a unit",
    'E1.ret': "the result of '{f}' needs a unit",
    'SI1.lib': "only 'si' can be used, not '{lib}'",
    'SI1.name': "si has no unit '{u}'",
    'E4': "units cannot be used inside an empirical function",
    'E5': "only built-in maths can be called inside an empirical function",
}


def format_error(err: CompileError, filename: str, source_lines: list) -> str:
    """file:line:col: error [ID]: message, then the source line and a caret."""
    out = f"{filename}:{err.line}:{err.col}: error [{err.rule}]: {err.message}"
    if 1 <= err.line <= len(source_lines):
        text = source_lines[err.line - 1].replace('\t', ' ')
        out += "\n    " + text + "\n    " + " " * (err.col - 1) + "^"
    return out


def format_errors(errors: list, filename: str, source: str) -> str:
    lines = source.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    parts = [format_error(e, filename, lines) for e in errors]
    n = len(errors)
    parts.append(f"{n} error" + ("" if n == 1 else "s") + (" (stopped after 20)" if n >= 20 else ""))
    return "\n".join(parts)
