"""Token types and the Token record (build guide Part 1). Frozen in phase 0."""
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # values
    NUMBER = auto()
    STRING = auto()
    NAME = auto()
    # keywords (D18: all reserved from day 1)
    UNIT = auto(); LET = auto(); FN = auto(); RETURN = auto(); PRINT = auto()
    IF = auto(); ELSE = auto(); WHILE = auto(); END = auto()
    IN = auto(); KIND = auto(); OF = auto(); OFFSET = auto(); DELTA = auto(); EMPIRICAL = auto()
    TRUE = auto(); FALSE = auto(); AND = auto(); OR = auto(); NOT = auto()
    READ = auto()                                            # D27
    USE = auto()                                             # D28
    # two-character symbols
    ARROW = auto(); EQEQ = auto(); NOTEQ = auto(); LE = auto(); GE = auto()
    # one-character symbols
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); CARET = auto()
    LPAREN = auto(); RPAREN = auto(); COMMA = auto(); COLON = auto(); EQUALS = auto()
    LT = auto(); GT = auto()
    # structure
    NEWLINE = auto()
    EOF = auto()


T = TokenType

KEYWORDS = {
    'unit': T.UNIT, 'let': T.LET, 'fn': T.FN, 'return': T.RETURN, 'print': T.PRINT,
    'if': T.IF, 'else': T.ELSE, 'while': T.WHILE, 'end': T.END,
    'in': T.IN, 'kind': T.KIND, 'of': T.OF, 'offset': T.OFFSET, 'delta': T.DELTA,
    'empirical': T.EMPIRICAL,
    'true': T.TRUE, 'false': T.FALSE, 'and': T.AND, 'or': T.OR, 'not': T.NOT,
    'read': T.READ, 'use': T.USE,
}

TWO_CHAR = {'->': T.ARROW, '==': T.EQEQ, '!=': T.NOTEQ, '<=': T.LE, '>=': T.GE}

ONE_CHAR = {
    '+': T.PLUS, '-': T.MINUS, '*': T.STAR, '/': T.SLASH, '^': T.CARET,
    '(': T.LPAREN, ')': T.RPAREN, ',': T.COMMA, ':': T.COLON, '=': T.EQUALS,
    '<': T.LT, '>': T.GT,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    text: str            # exactly as written
    value: object        # float for NUMBER, str for STRING, None otherwise
    line: int            # counted from 1
    col: int             # counted from 1
