"""The helper text copied into every generated file (build guide Part 10, D14, D16, D23)."""

US_PRINT_SOURCE = '''
def us_fmt(value, label):
    if isinstance(value, bool):          # bool first: in Python, bool is a kind of int
        return 'True' if value else 'False'
    if isinstance(value, str):
        return value
    if value != value or value in (float('inf'), float('-inf')):
        raise OverflowError('math range error')   # a result too large for a float
    if value == 0:
        value = 0.0                      # turns -0.0 into 0.0 (D16)
    text = format(value, '.10g')         # at most 10 significant digits (D16)
    return text + (' ' + label if label else '')

def us_print(*args):                     # value, label, value, label, ... (D23)
    if len(args) % 2:
        args = args + ('',)              # a single value with no label
    print(' '.join(us_fmt(v, l) for v, l in zip(args[0::2], args[1::2])))
'''


# D27: copied into the generated file only when the program uses read(...).
# US_UNITS (name -> (table, factor, offset)) is written by the generator after it.
US_READ_SOURCE = r'''
class UnitInputError(Exception):
    pass

def us_unit(text):
    """A typed unit such as 'lbf * s' or 'm / s^2' -> (table, factor, offset)."""
    import re
    toks = re.findall(r'[A-Za-z_][A-Za-z0-9_]*|\d+|\S', text)
    pos = [0]
    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else ''
    def take():
        t = peek()
        pos[0] += 1
        return t
    def combine(a, b, sign):
        out = dict(a)
        for k, p in b.items():
            out[k] = out.get(k, 0) + sign * p
            if out[k] == 0:
                del out[k]
        return out
    def factor():
        t = take()
        if t == '(':
            u = expr()
            if take() != ')':
                raise UnitInputError("missing ')' in the unit")
        elif t == '1':
            u = ({}, 1.0, 0.0)
        elif t in US_UNITS:
            u = US_UNITS[t]
        else:
            raise UnitInputError(f"unknown unit '{t}'" if t else 'the unit is incomplete')
        if peek() == '^':
            take()
            neg = peek() == '-'
            if neg:
                take()
            n = take()
            if not n.isdigit():
                raise UnitInputError('unit powers must be whole numbers')
            n = -int(n) if neg else int(n)
            if u[2]:
                raise UnitInputError('a unit with an offset cannot have a power')
            u = ({k: p * n for k, p in u[0].items()}, u[1] ** n, 0.0)
        return u
    def expr():
        u = factor()
        while peek() in ('*', '/'):
            op = take()
            v = factor()
            if u[2] or v[2]:
                raise UnitInputError('a unit with an offset cannot be part of a compound unit')
            if op == '*':
                u = (combine(u[0], v[0], 1), u[1] * v[1], 0.0)
            else:
                u = (combine(u[0], v[0], -1), u[1] / v[1], 0.0)
        return u
    u = expr()
    if peek():
        raise UnitInputError(f"unexpected '{peek()}' in the unit")
    return u

def us_read(prompt, want, label, reading, delta):
    """R1-R5: read 'number unit', check the unit against the declared one, return base units."""
    import re
    try:
        line = input(prompt)
    except EOFError:
        raise UnitInputError('no input')
    m = re.match(r'\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(.*?)\s*$', line)
    if not m:
        raise UnitInputError(f'expected a number with a unit, got {line.strip()!r}')
    value, text = float(m.group(1)), m.group(2)
    typed_delta = text.startswith('delta ')
    if typed_delta:
        text = text[6:].strip()
    if not text:
        if want:
            raise UnitInputError(f'a unit is required: type it like {value:g} {label}')
        return value
    table, factor, offset = us_unit(text)
    if {k: p for k, p in table.items() if k != 'rad'} != {k: p for k, p in want.items() if k != 'rad'}:
        raise UnitInputError(f'expected {label}, got {text}')
    if offset:
        if typed_delta and reading:
            raise UnitInputError('expected a temperature reading; leave out delta')
        if not typed_delta and not reading:
            raise UnitInputError(f'expected a change; type it like {value:g} delta {text}')
        return value * factor + (0.0 if typed_delta else offset)
    if typed_delta:
        raise UnitInputError("delta only applies to units with an offset")
    return value * factor
'''
