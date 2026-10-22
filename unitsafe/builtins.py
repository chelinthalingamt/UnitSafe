"""Built-in functions, constants and prelude units (build guide Part 5, D22, A1, A2)."""
import math

# name -> (number of arguments, Python text)
FUNCTIONS = {
    'sqrt': (1, 'math.sqrt'),
    'abs': (1, 'abs'),
    'exp': (1, 'math.exp'),
    'log': (1, 'math.log'),
    'sin': (1, 'math.sin'),
    'cos': (1, 'math.cos'),
    'tan': (1, 'math.tan'),
    'asin': (1, 'math.asin'),
    'acos': (1, 'math.acos'),
    'atan': (1, 'math.atan'),
    'atan2': (2, 'math.atan2'),
    'kelvin': (1, ''),            # D13: nothing to do at run time
}

TRIG = ('sin', 'cos', 'tan')
INVERSE_TRIG = ('asin', 'acos', 'atan')

CONSTANTS = {'pi': 'math.pi'}      # D22: a plain number

DEG_FACTOR = math.pi / 180         # 0.017453292519943295 (A2)

# D28: the SI catalogue for 'use si: ...'. Tables use base names directly (SI3).
from .units import UnitSpec, make  # noqa: E402

SI = {
    'm': UnitSpec(make({'m': 1})),
    's': UnitSpec(make({'s': 1})),
    'kg': UnitSpec(make({'kg': 1})),
    'A': UnitSpec(make({'A': 1})),
    'K': UnitSpec(make({'K': 1})),
    'mol': UnitSpec(make({'mol': 1})),
    'cd': UnitSpec(make({'cd': 1})),
    'N': UnitSpec(make({'kg': 1, 'm': 1, 's': -2})),
    'J': UnitSpec(make({'kg': 1, 'm': 2, 's': -2})),
    'W': UnitSpec(make({'kg': 1, 'm': 2, 's': -3})),
    'Pa': UnitSpec(make({'kg': 1, 'm': -1, 's': -2})),
    'Hz': UnitSpec(make({'s': -1})),
    'C': UnitSpec(make({'A': 1, 's': 1})),
    'V': UnitSpec(make({'kg': 1, 'm': 2, 's': -3, 'A': -1})),
    'ohm': UnitSpec(make({'kg': 1, 'm': 2, 's': -3, 'A': -2})),
    'km': UnitSpec(make({'m': 1}), 1000.0),
    'cm': UnitSpec(make({'m': 1}), 0.01),
    'mm': UnitSpec(make({'m': 1}), 0.001),
    'g': UnitSpec(make({'kg': 1}), 0.001),
    'min': UnitSpec(make({'s': 1}), 60.0),
    'h': UnitSpec(make({'s': 1}), 3600.0),
    'L': UnitSpec(make({'m': 3}), 0.001),
    'degC': UnitSpec(make({'K': 1}), 1.0, 273.15),                            # offset-aware (T1)
    'degF': UnitSpec(make({'K': 1}), 5 / 9, 459.67 * 5 / 9),                  # offset-aware (T1)
}
