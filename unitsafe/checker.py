"""Checker: gives every expression a QType and reports every broken rule
without stopping (build guide Parts 5-8; rules S1-S12, U1-U12, D7, D8 ...)."""
import dataclasses

from . import ast_nodes as A
from .builtins import CONSTANTS, DEG_FACTOR, FUNCTIONS, INVERSE_TRIG, TRIG
from .errors import MESSAGES, CompileError
from .symbols import Entry, FnSig, SymbolTable
from .units import (BOOL, ERROR, STRING, VOID, UnitSpec, ann_text, describe, div, half, label,
                    mul, num, power, spec_div, spec_mul, spec_pow, unit_text, without)


RAD = (('rad', 1),)

VERBS = {'+': 'add', '-': 'subtract', '*': 'multiply', '/': 'divide'}


def is_err(t) -> bool:
    return t is None or t.type == 'error'


def has_return(stmts) -> bool:
    for s in stmts:
        if isinstance(s, A.Return):
            return True
        if isinstance(s, A.If) and (has_return(s.then) or has_return(s.els or [])):
            return True
        if isinstance(s, A.While) and has_return(s.body):
            return True
    return False


def int_literal(node):
    """A whole-number literal (U10): Number written with digits only, or -Number."""
    if isinstance(node, A.Number) and node.text.isdigit():
        return int(node.text)
    if isinstance(node, A.Neg) and isinstance(node.operand, A.Number) and node.operand.text.isdigit():
        return -int(node.operand.text)
    return None


def integral_value(node):
    """For the U10 hint: 2.0 -> 2."""
    v = None
    if isinstance(node, A.Number):
        v = node.value
    elif isinstance(node, A.Neg) and isinstance(node.operand, A.Number):
        v = -node.operand.value
    return int(v) if v is not None and v == int(v) else None


class Checker:
    def __init__(self):
        self.errors = []
        self.syms = SymbolTable()
        self.fn = None            # (FnDecl, FnSig | None) while checking a body
        self.plain = False        # inside an empirical body (phase 10)
        g = self.syms.globals.names
        for name in FUNCTIONS:
            g[name] = Entry('builtin', 0)
        for name in CONSTANTS:
            g[name] = Entry('const', 0, qtype=num())
        # A1, A2: the prelude units
        g['rad'] = Entry('unit', 0, spec=UnitSpec(RAD), builtin=True)
        g['deg'] = Entry('unit', 0, spec=UnitSpec(RAD, DEG_FACTOR), builtin=True)

    # ---------- reporting ----------
    def report(self, rule, node, key=None, **kw):
        self.errors.append(CompileError(rule, node.line, node.col, MESSAGES[key or rule].format(**kw)))

    def declare_name(self, name, entry, node, category) -> bool:
        p = self.syms.problem(name, category)
        if p:
            rule, key, kw = p
            self.report(rule, node, key, **kw)
            return False
        self.syms.declare(name, entry)
        return True

    # ---------- driver ----------
    def run(self, program):
        self.pass1(program.body)
        for st in program.body:
            self.stmt(st, top=True)
        return sorted(self.errors, key=lambda e: (e.line, e.col))

    def pass1(self, body):
        """Units, kinds and function signatures, in order (Part 5 'The two passes')."""
        for st in body:
            if isinstance(st, A.UnitDecl):
                self.declare_unit(st)
            elif isinstance(st, A.KindDecl):
                self.declare_kind(st)
            elif isinstance(st, A.FnDecl):
                self.register_fn(st)

    def declare_unit(self, d):
        if d.expr is None:
            spec = UnitSpec(((d.name, 1),))                       # U1: a base unit
        else:
            spec = self.unit_definition(d)
            if spec is None:
                return
        if d.kind is not None:
            spec = self.unit_kind(d, spec)
            if spec is None:
                return
        self.declare_name(d.name, Entry('unit', d.line, spec=spec, delta_ok=spec.offset != 0), d, 'unit')

    def unit_definition(self, d):
        """unit km = 1000 m (C1-C3), nicknames (N1-N4); offsets come in phase 9."""
        rhs = self.resolve_unit_expr(d.expr, rule='C1')
        if rhs is None:
            return None
        n = 1.0 if d.number is None else d.number
        if n <= 0:                                                        # C3
            self.report('C3', d, 'C3.factor')
            return None
        if d.offset is not None:
            return self.offset_definition(d, n, rhs)
        return UnitSpec(rhs.table, n * rhs.factor, kind=rhs.kind)        # C2

    def offset_definition(self, d, n, rhs):
        """unit degC = 1 K offset 273.15 (T1): the offset is in the units of the right side."""
        if not isinstance(d.expr, A.UnitName) or rhs.offset != 0:
            self.report('T1', d)
            return None
        return UnitSpec(rhs.table, n * rhs.factor, d.offset * rhs.factor, rhs.kind)

    def unit_kind(self, d, spec):
        """unit J = N * m of energy (K1, K2)."""
        kind = self.kind_name(d.kind, d)
        if kind is None:
            return None
        if spec.kind is not None and spec.kind != kind:                  # K2
            self.report('K2', d, u=d.name, k=spec.kind)
            return None
        return dataclasses.replace(spec, kind=kind)

    def kind_name(self, name, node):
        e, _ = self.syms.lookup(name)
        if e is None or e.category != 'kind':                            # K1
            self.report('K1', node, k=name)
            return None
        return name

    def declare_kind(self, d):
        self.declare_name(d.name, Entry('kind', d.line), d, 'kind')

    def register_fn(self, f):
        entry = Entry('fn', f.line)
        if not self.declare_name(f.name, entry, f, 'fn'):
            return
        sig = FnSig(params=[(p.name, p.ann) for p in f.params], ret=f.ret, empirical=f.empirical,
                    returns_value=has_return(f.body))
        if f.empirical:
            self.register_empirical(f, entry, sig)
            return
        sig.param_types = [self.ann_type(p.ann) if p.ann is not None else num() for p in f.params]
        if f.ret is not None:
            sig.ret_type = self.ann_type(f.ret)
        else:
            sig.ret_type = num() if sig.returns_value else VOID
        entry.sig = sig

    def register_empirical(self, f, entry, sig):
        """E1: every parameter and the result need a unit; keep their specs for E3 and E6."""
        ok = True
        for p in f.params:
            if p.ann is None:
                self.report('E1', p, 'E1.param', p=p.name)
                ok = False
        if f.ret is None:
            self.report('E1', f, 'E1.ret', f=f.name)
            ok = False
        if not ok:
            return
        anns = [p.ann for p in f.params] + [f.ret]
        specs = [self.ann_spec(a) for a in anns]
        if any(sp is None for sp in specs):
            return
        types = [num(sp.table, sp.kind, reading=sp.offset != 0) for sp in specs]
        sig.param_specs, sig.ret_spec = specs[:-1], specs[-1]
        sig.param_types, sig.ret_type = types[:-1], types[-1]
        entry.sig = sig

    # ---------- unit expressions and annotations ----------
    def resolve_unit_expr(self, expr, rule='U1'):
        """UnitSpec for a written unit expression, or None after reporting (U1, C1, C5)."""
        if isinstance(expr, A.UnitName):
            e, _ = self.syms.lookup(expr.name)
            if e is None or e.category != 'unit':
                self.report(rule, expr, rule, u=expr.name)
                return None
            return e.spec
        if isinstance(expr, A.UnitOne):
            return UnitSpec(())
        if isinstance(expr, A.UnitPow):
            base = self.resolve_unit_expr(expr.base, rule)
            if base is None or not self.no_offset(expr.base, base):
                return None
            return spec_pow(base, expr.exp)
        left = self.resolve_unit_expr(expr.left, rule)
        right = self.resolve_unit_expr(expr.right, rule)
        if left is None or right is None:
            return None
        if not (self.no_offset(expr.left, left) and self.no_offset(expr.right, right)):
            return None
        return spec_mul(left, right) if isinstance(expr, A.UnitMul) else spec_div(left, right)

    def no_offset(self, expr, spec) -> bool:
        """T5: an offset unit may not be part of a compound unit or a power."""
        if spec.offset != 0:
            self.report('T5', expr, u=unit_text(expr))
            return False
        return True

    def ann_spec(self, ann):
        """The spec of a written annotation, with its kind settled (K1, K2)."""
        spec = self.resolve_unit_expr(ann.expr)
        if spec is None:
            return None
        if ann.kind is not None:
            kind = self.kind_name(ann.kind, ann)
            if kind is None:
                return None
            if spec.kind is not None and spec.kind != kind:              # K2
                self.report('K2', ann, u=unit_text(ann.expr), k=spec.kind)
                return None
            spec = dataclasses.replace(spec, kind=kind)
        return self.ann_spec_extra(ann, spec)

    def ann_spec_extra(self, ann, spec):
        if ann.delta:                                                     # T2
            if spec.offset == 0:
                self.report('T2', ann)
                return None
            return dataclasses.replace(spec, offset=0.0)
        return spec

    def ann_type(self, ann):
        spec = self.ann_spec(ann)
        return ERROR if spec is None else num(spec.table, spec.kind, reading=spec.offset != 0)

    # ---------- statements ----------
    def stmt(self, s, top=False):
        if isinstance(s, A.UnitDecl):
            if not top:
                self.report('S11', s, what='unit')
            return
        if isinstance(s, A.KindDecl):
            if not top:
                self.report('S11', s, what='kind')
            return
        if isinstance(s, A.FnDecl):
            if not top:
                self.report('S11', s, what='fn')
                return
            self.check_fn(s)
            return
        getattr(self, 'stmt_' + type(s).__name__)(s)

    def block(self, stmts):
        self.syms.push('block')
        for s in stmts:
            self.stmt(s)
        self.syms.pop()

    def stmt_Let(self, s):
        t = self.value(s.value)
        if s.ann is not None and self.plain:                              # E4
            self.report('E4', s.ann)
            vtype = ERROR
        elif s.ann is not None:
            target = self.ann_type(s.ann)
            self.fits(t, target, True, s.value, 'U8', 'U8', what=f"'{s.name}'")
            vtype = target if not is_err(target) else ERROR
        else:
            vtype = t
        self.declare_name(s.name, Entry('var', s.line, qtype=vtype, ann=s.ann), s, 'var')

    def stmt_Assign(self, s):
        e, crossed = self.syms.lookup(s.name)
        t = self.value(s.value)
        if e is None:
            self.report('S1', s, name=s.name)
        elif e.category != 'var':
            self.report('S12', s, 'S12.notvar', name=s.name, cat=e.category)
        elif crossed:
            self.report('D8', s, name=s.name)
        else:
            self.fits(t, e.qtype, e.ann is not None, s.value, 'U8', 'U8', what=f"'{s.name}'")

    def stmt_Print(self, s):
        for arg in s.args:
            t = self.expr(arg.value)
            if t.type == 'void':
                self.report('S10', arg.value, f=arg.value.name)
                continue
            if is_err(t):
                continue
            self.plan_print(arg, t)

    def plan_print(self, arg, t):
        """label, divisor, offset for one print value (D10, D11, C6, T6)."""
        explicit = arg.target is not None
        if explicit and self.plain:                                       # E4
            self.report('E4', arg.target)
            return
        if t.type != 'number':
            if explicit:
                self.report('C6', arg.target, a=f'a {t.type}', b=ann_text(arg.target))
            return
        ann = arg.target if explicit else self.declared_unit(arg.value)
        if ann is None:
            arg.label = self.nickname(t) or label(t.table)               # N3b
            return
        spec = self.ann_spec(ann)
        if spec is None:
            return
        a, b = t.table, spec.table
        a, b = without(a, 'rad'), without(b, 'rad')                       # D12
        if a != b:
            if explicit:                                                  # C6
                self.report('C6', arg.target, a=describe(t.table), b=describe(spec.table))
            else:
                arg.label = label(t.table)
            return
        if explicit and not self.target_extra(arg, t, spec):
            return
        reading = spec.offset != 0 and not ann.delta
        arg.label = ann_text(ann) if spec.table else ''                   # '-> 1' has no label
        arg.divisor = spec.factor
        arg.offset = spec.offset if reading else 0.0

    def nickname(self, t):
        """N3b: the one declared unit with exactly this table and kind, factor 1 and no offset.
        No match, or more than one (J and N * m both declared), means no nickname."""
        if not t.table:
            return None
        names = [name for name, e in self.syms.globals.names.items()
                 if e.category == 'unit' and e.spec.table == t.table and e.spec.kind == t.kind
                 and e.spec.factor == 1.0 and e.spec.offset == 0]
        return names[0] if len(names) == 1 else None

    def target_extra(self, arg, t, spec) -> bool:
        if spec.kind is not None and t.kind != spec.kind:                 # a kind cannot be converted away
            self.report('K3', arg.target, verb='convert', k1=t.kind or 'a plain value', k2=spec.kind)
            return False
        return self.target_temperature(arg, t, spec)

    def target_temperature(self, arg, t, spec) -> bool:                   # T6
        what = f"'{arg.value.name}'" if isinstance(arg.value, A.Name) else 'the value'
        u = unit_text(arg.target.expr)
        if arg.target.delta and t.reading:
            self.report('T6', arg.target, 'T6.reading', what=what)
            return False
        if not arg.target.delta and spec.offset != 0 and not t.reading:
            self.report('T6', arg.target, 'T6.change', what=what, u=u)
            return False
        return True

    def declared_unit(self, value):
        """D11: the written unit of an annotated variable, a call with '->', or a unit literal."""
        if isinstance(value, A.Name):
            e, _ = self.syms.lookup(value.name)
            if e is not None and e.category == 'var' and e.ann is not None:
                return e.ann
        elif isinstance(value, A.Call):
            e, _ = self.syms.lookup(value.name)
            if e is not None and e.category == 'fn' and e.sig is not None and e.sig.ret is not None:
                return e.sig.ret
        elif isinstance(value, A.UnitLiteral):
            pos = {'line': value.line, 'col': value.col}
            expr = A.UnitName(name=value.unit, **pos)
            if value.power != 1:
                expr = A.UnitPow(base=expr, exp=value.power, **pos)
            return A.UnitAnn(expr=expr, delta=value.delta, **pos)
        return None

    def condition(self, node):
        if isinstance(node, A.Compare):
            node.in_condition = True                                     # U12 wording
        t = self.value(node)
        if not is_err(t) and t.type != 'bool':
            self.report('S6', node, type=t.type)                         # S6

    def stmt_If(self, s):
        self.condition(s.cond)
        self.block(s.then)
        if s.els is not None:
            self.block(s.els)

    def stmt_While(self, s):
        self.condition(s.cond)
        self.block(s.body)

    def stmt_Return(self, s):
        t = self.value(s.value)
        if self.fn is None:
            self.report('S5', s)
            return
        f, sig = self.fn
        if sig is None or is_err(t):
            return
        if f.empirical:                                                    # the body is plain
            if t.type != 'number':
                self.report('S7', s.value, what=f"the result of '{f.name}'", t='number', v=t.type)
        elif f.ret is not None:
            self.fits(t, sig.ret_type, True, s.value, 'U9', 'U9.ret', what=f"the result of '{f.name}'", f=f.name)
        elif t.type != 'number':
            self.report('S7', s.value, what=f"the result of '{f.name}'", t='number', v=t.type)
        elif t.table:
            self.report('U9', s.value, 'U9.noresult', f=f.name, b=describe(t.table))

    def stmt_CallStmt(self, s):
        self.expr(s.call)

    def check_fn(self, f):
        e, _ = self.syms.lookup(f.name)
        sig = e.sig if (e is not None and e.category == 'fn' and e.line == f.line) else None
        self.syms.push('function')
        self.plain = f.empirical
        for i, p in enumerate(f.params):
            if f.empirical or sig is None:
                t, ann = num(), None
            else:
                t, ann = sig.param_types[i], p.ann
            self.declare_name(p.name, Entry('var', p.line, qtype=t, ann=ann), p, 'var')
        self.fn = (f, sig)
        for s in f.body:
            self.stmt(s)
        if f.ret is not None and (not f.body or not isinstance(f.body[-1], A.Return)):
            self.report('S8', f, 'S8b', f=f.name)                        # S8b
        self.fn = None
        self.plain = False
        self.syms.pop()

    # ---------- the one store function ----------
    def fits(self, value, target, declared, node, rule, key, what, **kw) -> bool:
        if is_err(value) or is_err(target) or value.type == 'void':
            return True
        if value.type != target.type:                                      # S7
            self.report('S7', node, what=what, t=target.type, v=value.type)
            return False
        if value.type != 'number':
            return True
        a, b = value.table, target.table
        if declared:                                                       # D12
            a, b = without(a, 'rad'), without(b, 'rad')
        if a != b:                                                         # U8 / U9
            self.report(rule, node, key, what=what, a=describe(target.table), b=describe(value.table), **kw)
            return False
        return self.fits_extra(value, target, declared, node, what)

    def fits_extra(self, value, target, declared, node, what) -> bool:
        tk, vk = target.kind, value.kind                                   # K5
        if tk != vk:
            if tk is None:
                self.report('K5', node, 'K5.plain', what=what, k=vk)
                return False
            if vk is not None:
                self.report('K5', node, what=what, k1=tk, k2=vk)
                return False
        return self.fits_temperature(value, target, node, what)

    def fits_temperature(self, value, target, node, what) -> bool:       # T8 (T-store)
        if target.reading and not value.reading:
            self.report('T8', node, 'T8.reading', what=what)
            return False
        if value.reading and not target.reading:
            self.report('T8', node, 'T8.change', what=what)
            return False
        return True

    # ---------- expressions ----------
    def expr(self, node):
        t = getattr(self, 'ex_' + type(node).__name__)(node)
        node.qtype = t
        return t

    def value(self, node):
        """An expression that must give a value (S9)."""
        t = self.expr(node)
        if t.type == 'void':
            self.report('S9', node, f=node.name)
            return ERROR
        return t

    def ex_Number(self, node):
        return num()                                                       # U5

    def ex_String(self, node):
        return STRING

    def ex_Bool(self, node):
        return BOOL

    def ex_UnitLiteral(self, node):                                        # U1, U3, D1
        if self.plain:
            self.report('E4', node)
            return ERROR
        e, _ = self.syms.lookup(node.unit)
        if e is None or e.category != 'unit':
            if e is not None and e.category == 'var':
                self.report('U1', node, 'U1.var', u=node.unit, n=node.text)
            else:
                self.report('U1', node, u=node.unit)
            return ERROR
        return self.literal_type(node, e)

    def literal_type(self, node, e):
        spec = e.spec
        if node.delta and spec.offset == 0:                               # T2
            self.report('T2', node)
            return ERROR
        if node.power != 1:
            if spec.offset != 0:                                          # T5
                self.report('T5', node, u=node.unit)
                return ERROR
            spec = spec_pow(spec, node.power)
        reading = spec.offset != 0 and not node.delta                    # T2, T4
        node.base_value = node.value * spec.factor + (spec.offset if reading else 0.0)
        return num(spec.table, spec.kind, reading)

    def ex_Name(self, node):
        e, crossed = self.syms.lookup(node.name)
        if e is None:
            self.report('S1', node, name=node.name)
            return ERROR
        if e.category == 'var':
            if crossed:
                self.report('D8', node, name=node.name)
                return ERROR
            return e.qtype
        if e.category == 'unit':                                          # U4
            if self.plain:
                self.report('E4', node)
                return ERROR
            return self.unit_as_value(node, e)
        if e.category == 'const':                                          # D22
            node.const = CONSTANTS[node.name]
            return num()
        if e.category == 'kind':
            self.report('S12', node, 'S12.kind', name=node.name)
            return ERROR
        self.report('S12', node, 'S12.value', name=node.name, cat='function')
        return ERROR

    def unit_as_value(self, node, e):
        if e.spec.offset != 0:                                            # T5b
            self.report('T5', node, 'T5b', u=node.name)
            return ERROR
        node.unit_value = e.spec.factor
        return num(e.spec.table, e.spec.kind)

    def ex_BinOp(self, node):
        L, R = self.value(node.left), self.value(node.right)
        if is_err(L) or is_err(R):
            return ERROR
        for t in (L, R):
            if t.type != 'number':
                self.report('S3', node, verb=VERBS[node.op], type=t.type)
                return ERROR
        if node.op in ('+', '-'):
            if L.table != R.table:                                         # U6
                self.report('U6', node, verb=VERBS[node.op], a=describe(L.table), b=describe(R.table), where='')
                return ERROR
            return self.add_result(node, L, R)
        return self.mul_result(node, L, R)

    def kinds_match(self, node, L, R, verb) -> bool:                      # K3
        if L.kind == R.kind:
            return True
        if L.kind is None or R.kind is None:
            self.report('K3', node, 'K3.plain', verb=verb, k=L.kind or R.kind)
        else:
            self.report('K3', node, verb=verb, k1=L.kind, k2=R.kind)
        return False

    def add_result(self, node, L, R):
        if not self.kinds_match(node, L, R, VERBS[node.op]):
            return ERROR
        return self.add_temperature(node, L, R)

    def add_temperature(self, node, L, R):                                # T3
        if node.op == '+':
            if L.reading and R.reading:
                self.report('T3', node, 'T3.add')
                return ERROR
            reading = L.reading or R.reading
        else:
            if L.reading and R.reading:
                reading = False                                           # reading - reading = change
            elif R.reading:
                self.report('T3', node, 'T3.sub')
                return ERROR
            else:
                reading = L.reading
        return num(L.table, L.kind, reading)

    @staticmethod
    def is_plain_number(t) -> bool:
        return not t.table and t.kind is None

    def mul_result(self, node, L, R):                                     # U7, K4, K4b
        if not self.mul_temperature(node, L, R):
            return ERROR
        table = mul(L.table, R.table) if node.op == '*' else div(L.table, R.table)
        kind = None
        if self.is_plain_number(R):
            kind = L.kind
        elif node.op == '*' and self.is_plain_number(L):
            kind = R.kind
        return num(table, kind)

    def mul_temperature(self, node, L, R) -> bool:                        # T3, T5
        for side, t in ((node.left, L), (node.right, R)):
            if t.reading:
                if isinstance(side, A.UnitLiteral):
                    self.report('T5', side, u=side.unit)
                else:
                    self.report('T3', node, 'T3.op', op=VERBS[node.op])
                return False
        return True

    def ex_Compare(self, node):
        L, R = self.value(node.left), self.value(node.right)
        if is_err(L) or is_err(R):
            return ERROR
        if L.type != R.type:
            self.report('S3', node, 'S3.mixed', a=L.type, b=R.type)
            return ERROR
        if L.type in ('string', 'bool'):
            if node.op not in ('==', '!='):
                self.report('S3', node, 'S3.order')
                return ERROR
            return BOOL
        if L.table != R.table:                                             # U6, U12
            self.report('U6', node, verb='compare', a=describe(L.table), b=describe(R.table),
                        where=' in this condition' if node.in_condition else '')
            return ERROR
        if not self.compare_extra(node, L, R):
            return ERROR
        return BOOL

    def compare_extra(self, node, L, R) -> bool:
        return self.kinds_match(node, L, R, 'compare') and self.compare_temperature(node, L, R)

    def compare_temperature(self, node, L, R) -> bool:                    # T3
        if L.reading != R.reading:
            self.report('T3', node, 'T3.cmp')
            return False
        return True

    def ex_Logic(self, node):                                              # D20
        ok = True
        for side in (node.left, node.right):
            t = self.value(side)
            if is_err(t):
                ok = False
            elif t.type != 'bool':
                self.report('S3', side, 'S3.logic', op=node.op, type=t.type)
                ok = False
        return BOOL if ok else ERROR

    def ex_Not(self, node):
        t = self.value(node.operand)
        if is_err(t):
            return ERROR
        if t.type != 'bool':
            self.report('S3', node, 'S3.logic', op='not', type=t.type)
            return ERROR
        return BOOL

    def ex_Neg(self, node):                                                # D2
        t = self.value(node.operand)
        if is_err(t):
            return ERROR
        if t.type != 'number':
            self.report('S3', node, verb='negate', type=t.type)
            return ERROR
        return self.neg_result(node, t)

    def neg_result(self, node, t):                                         # T3
        if t.reading:
            self.report('T3', node, 'T3.op', op='negate')
            return ERROR
        return t

    def ex_Power(self, node):                                              # U10
        B, E = self.value(node.base), self.value(node.exp)
        if is_err(B) or is_err(E):
            return ERROR
        for t in (B, E):
            if t.type != 'number':
                self.report('S3', node, verb='raise', type=t.type)
                return ERROR
        if E.table:
            self.report('U10', node.exp, 'U10b', a=describe(E.table))
            return ERROR
        if not self.power_extra(node, B):
            return ERROR
        if not B.table:
            return num()
        n = int_literal(node.exp)
        if n is None:
            hint = integral_value(node.exp)
            if hint is not None:
                self.report('U10', node.exp, 'U10.hint', n=hint)
            else:
                self.report('U10', node.exp)
            return ERROR
        return num(power(B.table, n))

    def power_extra(self, node, B) -> bool:                               # T3
        if B.reading:
            self.report('T3', node, 'T3.op', op='raise')
            return False
        return True

    def ex_Call(self, node):
        e, _ = self.syms.lookup(node.name)
        if e is None:
            for a in node.args:
                self.expr(a)
            self.report('S1', node, name=node.name)
            return ERROR
        if e.category == 'builtin':
            return self.builtin_call(node)
        if e.category != 'fn':
            for a in node.args:
                self.expr(a)
            self.report('S12', node, 'S12.notfn', name=node.name)
            return ERROR
        if self.plain:                                                     # E5
            for a in node.args:
                self.expr(a)
            self.report('E5', node)
            return ERROR
        return self.user_call(node, e.sig)

    def user_call(self, node, sig):
        ts = [self.value(a) for a in node.args]
        if sig is None:
            return ERROR
        if len(ts) != len(sig.params):                                     # S4
            self.report('S4', node, f=node.name, n=len(sig.params), m=len(ts))
            return ERROR
        for (pname, _), ptype, arg, t in zip(sig.params, sig.param_types, node.args, ts):
            self.fits(t, ptype, True, arg, 'U9', 'U9.arg', what=f"argument '{pname}'", p=pname)
        return self.call_result(node, sig)

    def call_result(self, node, sig):
        if sig.empirical:                                                  # E3, E6
            node.arg_scale = [(sp.factor, sp.offset) for sp in sig.param_specs]
            node.ret_scale = (sig.ret_spec.factor, sig.ret_spec.offset)
        return sig.ret_type

    def builtin_call(self, node):
        name = node.name
        arity, py = FUNCTIONS[name]
        ts = [self.value(a) for a in node.args]
        if len(ts) != arity:                                               # S4
            self.report('S4', node, f=name, n=arity, m=len(ts))
            return ERROR
        if any(is_err(t) for t in ts):
            return ERROR
        for t in ts:
            if t.type != 'number':
                self.report('S3', node, 'S3.fnarg', f=name, type=t.type)
                return ERROR
        node.py_func = py
        t = ts[0]
        if not self.builtin_extra(node, ts):
            return ERROR
        if name == 'sqrt':                                                 # U11
            h = half(t.table)
            if h is None:
                self.report('U11', node, 'U11.odd', a=describe(t.table))
                return ERROR
            return num(h)
        if name == 'abs':
            return t
        if name == 'kelvin':
            return self.kelvin(node, t)
        if name == 'atan2':
            if ts[0].table != ts[1].table:
                self.report('A4', node, 'U11.atan2',
                            a=describe(ts[0].table), b=describe(ts[1].table))
                return ERROR
            return self.angle_result()
        if name in TRIG:
            return self.trig(node, t)
        if t.table:                                                        # exp, log, asin, acos, atan
            rule = 'A4' if name in INVERSE_TRIG else 'U11'
            self.report(rule, node, 'U11.nounit', f=name, a=describe(t.table))
            return ERROR
        return self.angle_result() if name in INVERSE_TRIG else num()

    def builtin_extra(self, node, ts) -> bool:                            # T3
        if node.name != 'kelvin' and any(t.reading for t in ts):
            self.report('T3', node, 'T3.op', op=f'take {node.name} of')
            return False
        return True

    def trig(self, node, t):                                               # A3
        if self.plain:                                                     # plain mode: no units to check
            if t.table:
                self.report('U11', node, 'U11.nounit', f=node.name, a=describe(t.table))
                return ERROR
            return num()
        if t.table == RAD:                                                 # A3
            return num()
        arg = node.args[0]
        if t.table:
            self.report('A3', node, f=node.name, a=describe(t.table))
        elif isinstance(arg, A.Number):                                    # A6
            self.report('A3', node, 'A3.plain', f=node.name, n=arg.text)
        elif isinstance(arg, A.Name) and arg.name == 'pi':
            self.report('A3', node, 'A3.pi', f=node.name)
        else:
            self.report('A3', node, 'A3.plainvar', f=node.name)
        return ERROR

    def angle_result(self):                                                # A4
        return num() if self.plain else num(RAD)

    def kelvin(self, node, t):                                             # D13
        if not t.reading:
            self.report('D13', node)
            return ERROR
        return num(t.table, t.kind, False)


def check(program) -> list:
    return Checker().run(program)
