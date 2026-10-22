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
