"""Symbol table and scopes (build guide Part 5, U2, N4, K6, S2, S2c, D7, D8)."""
from dataclasses import dataclass, field


@dataclass
class FnSig:
    params: list                  # [(name, UnitAnn | None)]
    ret: object                   # UnitAnn | None
    empirical: bool
    returns_value: bool           # has at least one return statement
    param_types: list = field(default_factory=list)
    ret_type: object = None
    param_specs: list = field(default_factory=list)   # empirical edges (E3)
    ret_spec: object = None


@dataclass
class Entry:
    category: str                 # 'var', 'fn', 'unit', 'kind', 'builtin', 'const'
    line: int
    qtype: object = None          # var: its type, fixed for life (S7, U8)
    ann: object = None            # var: its written annotation (D11, K5)
    spec: object = None           # unit: what it means
    delta_ok: bool = False        # unit: has an offset (T2)
    sig: FnSig | None = None      # fn
    builtin: bool = False         # unit: from the prelude (rad, deg)


class Scope:
    def __init__(self, kind: str, parent):     # kind: 'global', 'function' or 'block'
        self.kind = kind
        self.parent = parent
        self.names = {}


GLOBAL_ONLY = ('unit', 'kind', 'fn', 'builtin', 'const')


class SymbolTable:
    def __init__(self):
        self.globals = Scope('global', None)
        self.current = self.globals

    def push(self, kind: str):
        self.current = Scope(kind, self.current)

    def pop(self):
        self.current = self.current.parent

    def lookup(self, name: str):
        """Return (entry, crossed_function_boundary). Missing name: (None, False)."""
        scope, crossed = self.current, False
        while scope is not None:
            if name in scope.names:
                return scope.names[name], crossed
            if scope.kind == 'function':
                crossed = True
            scope = scope.parent
        return None, False

    def problem(self, name: str, category: str):
        """Why `name` cannot be declared here as `category`: (rule, key, kwargs) or None."""
        g = self.globals.names.get(name)
        if g is not None and category == 'kind':                         # K6
            return 'K6', 'K6', {'k': name}
        if g is not None and g.category in GLOBAL_ONLY:                  # 1. U2, N4, K6, S2c
            if g.category == 'unit':
                if g.builtin and category == 'unit':
                    return 'C3', 'C3.builtin', {'u': name}
                return ('C3', 'C3', {'u': name}) if category == 'unit' else ('U2', 'U2', {'name': name})
            if g.category == 'kind':
                return 'K6', 'K6', {'k': name}
            if g.category == 'fn':
                return 'S2', 'S2.fn', {'name': name}
            return 'S2c', 'S2c', {'name': name}
        if g is not None and category in ('unit', 'kind', 'fn'):        # a global variable already
            if category == 'unit':
                return 'U2', 'U2.var', {'name': name}
            if category == 'kind':
                return 'K6', 'K6', {'k': name}
            return 'S2', 'S2', {'name': name, 'n': g.line}
        same = self.current.names.get(name)
        if same is not None:                                             # 2. S2
            return 'S2', 'S2', {'name': name, 'n': same.line}
        if category == 'var' and self.current.kind == 'block':           # 3. D7
            scope = self.current.parent
            while scope is not None:
                e = scope.names.get(name)
                if e is not None and e.category == 'var':
                    return 'D7', 'D7', {'name': name, 'n': e.line}
                if scope.kind in ('function', 'global'):
                    break
                scope = scope.parent
        return None

    def declare(self, name: str, entry: Entry):
        self.current.names[name] = entry
