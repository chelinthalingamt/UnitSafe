"""The helper text copied into every generated file (build guide Part 10, D14, D16, D23)."""

US_PRINT_SOURCE = '''
def us_fmt(value, label):
    if isinstance(value, bool):          # bool first: in Python, bool is a kind of int
        return 'True' if value else 'False'
    if isinstance(value, str):
        return value
    if value == 0:
        value = 0.0                      # turns -0.0 into 0.0 (D16)
    text = format(value, '.10g')         # at most 10 significant digits (D16)
    return text + (' ' + label if label else '')

def us_print(*args):                     # value, label, value, label, ... (D23)
    if len(args) % 2:
        args = args + ('',)              # a single value with no label
    print(' '.join(us_fmt(v, l) for v, l in zip(args[0::2], args[1::2])))
'''
