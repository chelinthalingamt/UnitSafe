# UnitSafe

A small language where every number carries a unit. The compiler checks the units
before the program runs, then turns it into plain Python with no unit code left in it.

```
unit m
unit s
let v = 120 m / 10 s
print(v)              # 12 m / s
print(v + 3 m)        # error [U6]: cannot add m / s and m
```

## Run it

Needs Python 3.10 or newer. Nothing to install.

```
python -m unitsafe run   program.us            # check, compile and run
python -m unitsafe build program.us -o out.py  # write the Python file (it runs on its own)
python -m unitsafe check program.us            # check only
python -m unitsafe tokens program.us           # debugging: the tokens
python -m unitsafe ast    program.us           # debugging: the tree
```

Exit codes: 0 ok, 1 compile errors, 2 run-time error, 3 usage or file problem.

## Tests

```
python run_tests.py          # or: python -m pytest
```

Every rule in the build guide has tests (about 270 table rows, plus 500 random property
checks): `tests/test_lexer.py`, `test_parser.py`, `test_units.py`, `test_checker.py`,
`test_run.py`, the extension tests (`test_ext_*.py`), the demo and erasure tests, and the
10 sample programs in `tests/programs` (each `.us` file with its `.expected` output).
The tests use only the standard library (`unittest`).

## Demos

```
python demo.py review2      # version 1: a valid run, a unit error, the generated Python, several errors at once
python demo.py review3      # extensions: conversions, angles, kinds, temperatures, empirical functions
```

## Layout

| Path | What it is |
| --- | --- |
| `unitsafe/tokens.py`, `ast_nodes.py` | the contract between stages |
| `unitsafe/lexer.py` | text to tokens (L1-L8) |
| `unitsafe/parser.py` | tokens to tree (P1-P6) |
| `unitsafe/units.py` | unit tables and their maths |
| `unitsafe/symbols.py`, `builtins.py` | names, scopes, built-in functions and units |
| `unitsafe/checker.py` | every meaning rule (S, U, C, N, A, K, T, E, D) |
| `unitsafe/codegen.py`, `runtime.py` | Python output and the print helper |
| `unitsafe/cli.py` | the command line |
| `docs/grammar.txt` | the full grammar |
| `tests/` | the test suite |

The build guide is the reference for every rule ID used in the code and tests.
