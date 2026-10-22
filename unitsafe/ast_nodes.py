"""AST node classes (build guide Part 2, plus D19-D23). Frozen in phase 0.

Every node keeps line and col (P4). They are left out of == so parser tests
compare trees by shape. Fields the checker fills in start empty and are also
left out of ==.
"""
from dataclasses import dataclass, field, fields


def _cf(default=None):
    """A checker-filled field: starts empty, ignored by == and repr."""
    return field(default=default, compare=False, repr=False)


@dataclass(kw_only=True)
class Node:
    line: int = field(compare=False, repr=False)
    col: int = field(compare=False, repr=False)


# ---------- unit expressions: appear only where a unit is written ----------
@dataclass(kw_only=True)
class UnitName(Node):
    name: str


@dataclass(kw_only=True)
class UnitOne(Node):          # the 1 in 1 / s
    pass


@dataclass(kw_only=True)
class UnitMul(Node):
    left: Node
    right: Node


@dataclass(kw_only=True)
class UnitDiv(Node):
    left: Node
    right: Node


@dataclass(kw_only=True)
class UnitPow(Node):
    base: Node
    exp: int                  # may be negative, never 0


@dataclass(kw_only=True)
class UnitAnn(Node):          # what follows ':' '->' or 'in'
    expr: Node
    delta: bool = False       # phase 9
    kind: str | None = None   # phase 8


# ---------- expressions ----------
@dataclass(kw_only=True)
class Number(Node):
    value: float
    text: str
    qtype: object = _cf()


@dataclass(kw_only=True)
class UnitLiteral(Node):      # NUMBER unitAtom (U3, D1, D17)
    value: float
    text: str
    unit: str
    power: int = 1
    delta: bool = False
    qtype: object = _cf()
    base_value: float | None = _cf()   # the number in base units (C4, T4)


@dataclass(kw_only=True)
class String(Node):
    value: str
    qtype: object = _cf()


@dataclass(kw_only=True)
class Bool(Node):             # D19
    value: bool
    qtype: object = _cf()


@dataclass(kw_only=True)
class Name(Node):
    name: str
    qtype: object = _cf()
    unit_value: float | None = _cf()   # set when a unit is used as a value (U4)
    const: str | None = _cf()          # Python text for a built-in constant (D22)


@dataclass(kw_only=True)
class BinOp(Node):            # + - * /   (position = the operator)
    op: str
    left: Node
    right: Node
    qtype: object = _cf()


@dataclass(kw_only=True)
class Compare(Node):          # < > <= >= == !=   (position = the operator)
    op: str
    left: Node
    right: Node
    qtype: object = _cf()
    in_condition: bool = _cf(False)    # U12 wording


@dataclass(kw_only=True)
class Logic(Node):            # and, or (D20)
    op: str
    left: Node
    right: Node
    qtype: object = _cf()


@dataclass(kw_only=True)
class Not(Node):              # D20
    operand: Node
    qtype: object = _cf()


@dataclass(kw_only=True)
class Neg(Node):              # D2
    operand: Node
    qtype: object = _cf()


@dataclass(kw_only=True)
class Power(Node):
    base: Node
    exp: Node
    qtype: object = _cf()


@dataclass(kw_only=True)
class Read(Node):             # D27: read("prompt", unit)
    prompt: str | None
    ann: UnitAnn
    qtype: object = _cf()
    want: dict | None = _cf()          # the declared table, checked when the program runs
    label: str = _cf('')
    reading: bool = _cf(False)
    delta: bool = _cf(False)


@dataclass(kw_only=True)
class Call(Node):
    name: str
    args: list
    qtype: object = _cf()
    py_func: str | None = _cf()        # e.g. 'math.sin' for a built-in
    arg_scale: list | None = _cf()     # [(divisor, offset), ...] at an empirical edge (E3)
    ret_scale: tuple | None = _cf()    # (factor, offset) for an empirical result


# ---------- statements ----------
@dataclass(kw_only=True)
class UnitDecl(Node):
    name: str
    number: float | None = None
    expr: Node | None = None
    offset: float | None = None
    kind: str | None = None


@dataclass(kw_only=True)
class UseDecl(Node):          # D28: use si: m, s, kg
    lib: str
    names: list               # UnitName nodes, for positions in errors


@dataclass(kw_only=True)
class KindDecl(Node):
    name: str


@dataclass(kw_only=True)
class Let(Node):
    name: str
    ann: UnitAnn | None
    value: Node


@dataclass(kw_only=True)
class Assign(Node):
    name: str
    value: Node


@dataclass(kw_only=True)
class PrintArg(Node):         # D23
    value: Node
    target: UnitAnn | None = None      # the 'in' part
    label: str = _cf('')
    divisor: float = _cf(1.0)
    offset: float = _cf(0.0)


@dataclass(kw_only=True)
class Print(Node):
    args: list


@dataclass(kw_only=True)
class If(Node):
    cond: Node
    then: list
    els: list | None = None
    elif_chain: bool = False           # D21


@dataclass(kw_only=True)
class While(Node):
    cond: Node
    body: list


@dataclass(kw_only=True)
class Param(Node):
    name: str
    ann: UnitAnn | None = None


@dataclass(kw_only=True)
class FnDecl(Node):
    name: str
    params: list
    ret: UnitAnn | None
    body: list
    empirical: bool = False


@dataclass(kw_only=True)
class Return(Node):
    value: Node


@dataclass(kw_only=True)
class CallStmt(Node):         # D6
    call: Call


@dataclass(kw_only=True)
class Program(Node):
    body: list
    uses_read: bool = _cf(False)       # D27: the generator adds the input helper
    unit_table: dict | None = _cf()    # D27: name -> (table, factor, offset)


def dump(node, indent=0) -> str:
    """Readable tree for 'unitsafe ast'."""
    pad = '  ' * indent
    if isinstance(node, list):
        return '\n'.join(dump(n, indent) for n in node)
    if not isinstance(node, Node):
        return pad + repr(node)
    simple, children = [], []
    for f in fields(node):
        if not f.compare:
            continue
        v = getattr(node, f.name)
        if isinstance(v, Node) or (isinstance(v, list) and v and isinstance(v[0], Node)):
            children.append((f.name, v))
        elif v not in (None, False, []) or f.name in ('value',):
            simple.append(f"{f.name}={v!r}")
    out = f"{pad}{type(node).__name__}({', '.join(simple)})  @{node.line}:{node.col}"
    for name, v in children:
        out += f"\n{pad}  {name}:"
        out += "\n" + dump(v, indent + 2)
    return out
