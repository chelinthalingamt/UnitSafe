"""The theory of the language: unit tables and the two records (build guide Part 4).

A table is a tuple of (base, power) pairs, sorted by base name, with no zero
powers, so == is always the right test (U6).
"""
from dataclasses import dataclass

from . import ast_nodes as A

Table = tuple


def make(d: dict) -> Table:
    return tuple(sorted((b, p) for b, p in d.items() if p != 0))


def mul(a: Table, b: Table) -> Table:                     # U7
    out = dict(a)
    for base, p in b:
        out[base] = out.get(base, 0) + p
    return make(out)


def div(a: Table, b: Table) -> Table:                     # U7
    return mul(a, tuple((base, -p) for base, p in b))


def power(a: Table, n: int) -> Table:                     # U10
    return make({b: p * n for b, p in a})


def half(a: Table):                                       # U11; None means an odd power
    if any(p % 2 for _, p in a):
        return None
    return make({b: p // 2 for b, p in a})


def without(a: Table, base: str) -> Table:                # D12: compare ignoring rad
    return tuple((b, p) for b, p in a if b != base)


def label(a: Table) -> str:                               # for print; '' for no unit
    top = [b if p == 1 else f'{b}^{p}' for b, p in a if p > 0]
    bot = [b if p == -1 else f'{b}^{-p}' for b, p in a if p < 0]
    if not top and not bot:
        return ''
    text = ' * '.join(top) or '1'
    if bot:
        den = ' * '.join(bot)
        text += ' / ' + (f'({den})' if len(bot) > 1 else den)
    return text


def describe(a: Table) -> str:                            # for error messages
    return label(a) or 'no unit'


@dataclass(frozen=True)
class UnitSpec:                   # what a written unit means
    table: Table
    factor: float = 1.0           # C2: base units per one of these
    offset: float = 0.0           # T1: kelvin = number * factor + offset
    kind: str | None = None       # K2


@dataclass(frozen=True)
class QType:                      # what an expression is
    type: str                     # 'number', 'bool', 'string', 'void' or 'error'
    table: Table = ()
    kind: str | None = None       # K rules
    reading: bool = False         # T2: a temperature reading on an offset scale


BOOL = QType('bool')
STRING = QType('string')
VOID = QType('void')
ERROR = QType('error')


def num(table=(), kind=None, reading=False) -> QType:
    return QType('number', table, kind, reading)


def spec_mul(a, b):                                       # C5
    return UnitSpec(mul(a.table, b.table), a.factor * b.factor)


def spec_div(a, b):                                       # C5
    return UnitSpec(div(a.table, b.table), a.factor / b.factor)


def spec_pow(a, n):                                       # C5
    return UnitSpec(power(a.table, n), a.factor ** n)


def unit_text(expr) -> str:
    """A written unit expression back as text, for print labels."""
    if isinstance(expr, A.UnitName):
        return expr.name
    if isinstance(expr, A.UnitOne):
        return '1'
    if isinstance(expr, A.UnitPow):
        base = unit_text(expr.base)
        if not isinstance(expr.base, (A.UnitName, A.UnitOne)):
            base = f'({base})'
        return f'{base}^{expr.exp}'
    if isinstance(expr, A.UnitMul):
        return f'{unit_text(expr.left)} * {unit_text(expr.right)}'
    if isinstance(expr, A.UnitDiv):
        right = unit_text(expr.right)
        if isinstance(expr.right, (A.UnitMul, A.UnitDiv)):
            right = f'({right})'
        return f'{unit_text(expr.left)} / {right}'
    raise TypeError(expr)


def ann_text(ann) -> str:
    """Label for a written annotation or 'in' target, with 'delta ' when present."""
    return ('delta ' if ann.delta else '') + unit_text(ann.expr)
