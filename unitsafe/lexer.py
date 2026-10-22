"""Lexer: characters to tokens (build guide Part 1, rules L1-L8, D4, D5)."""
import math
import string

from .errors import CompileError, LexError
from .tokens import KEYWORDS, ONE_CHAR, TWO_CHAR, Token, TokenType as T

ASCII_LETTERS = set(string.ascii_letters)
DIGITS = set('0123456789')
NAME_CHARS = ASCII_LETTERS | DIGITS | {'_'}


class Lexer:
    def __init__(self, source: str):
        self.text = source.replace('\r\n', '\n').replace('\r', '\n')
        self.i = 0
        self.line = 1
        self.col = 1
        self.depth = 0            # bracket depth (D4)
        self.tokens = []

    # ---------- helpers ----------
    def at_end(self) -> bool:
        return self.i >= len(self.text)

    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.text[j] if j < len(self.text) else ''

    def advance(self) -> str:
        c = self.text[self.i]
        self.i += 1
        if c == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def add(self, type_, text, value, line, col):
        self.tokens.append(Token(type_, text, value, line, col))

    def error(self, rule, msg, line, col):
        return LexError(CompileError(rule, line, col, msg))

    # ---------- main loop ----------
    def run(self) -> list:
        while not self.at_end():
            c = self.peek()
            if c in ' \t':                                   # L2
                self.advance()
            elif c == '#':                                   # L2: comment, keep the '\n'
                while not self.at_end() and self.peek() != '\n':
                    self.advance()
            elif c == '\n':
                line, col = self.line, self.col
                self.advance()
                self.newline(line, col)
            elif c in DIGITS:
                self.number()                                # L5, D5
            elif c in ASCII_LETTERS or c == '_':
                self.name_or_keyword()                       # L4
            elif c == '"':
                self.string()                                # L6
            else:
                self.symbol()                                # L3, else L7
        self.newline(self.line, self.col)                    # L8
        self.add(T.EOF, '', None, self.line, self.col)
        return self.tokens

    def newline(self, line, col):
        """Only at bracket depth 0, never twice in a row, never first (NEWLINE rules)."""
        if self.depth == 0 and self.tokens and self.tokens[-1].type != T.NEWLINE:
            self.add(T.NEWLINE, '\n', None, line, col)

    # ---------- token kinds ----------
    def number(self):
        start, line, col = self.i, self.line, self.col
        while self.peek() in DIGITS and self.peek():
            self.advance()
        if self.peek() == '.':
            if self.peek(1) and self.peek(1) in DIGITS:
                self.advance()
                while self.peek() and self.peek() in DIGITS:
                    self.advance()
            else:
                self.advance()
                raise self.error('L5', f"malformed number '{self.text[start:self.i]}'", line, col)
        # D5: exponent only if a digit (or a sign and a digit) really follows
        if self.peek() in ('e', 'E') and self.peek():
            n1, n2 = self.peek(1), self.peek(2)
            if (n1 and n1 in DIGITS) or (n1 in ('+', '-') and n1 and n2 and n2 in DIGITS):
                self.advance()
                if self.peek() in ('+', '-'):
                    self.advance()
                while self.peek() and self.peek() in DIGITS:
                    self.advance()
        if self.peek() == '.':                               # 3.4.5
            while self.peek() and (self.peek() in DIGITS or self.peek() == '.'):
                self.advance()
            raise self.error('L5', f"malformed number '{self.text[start:self.i]}'", line, col)
        if self.peek() == '_':                               # 1_000
            raise self.error('L5', 'digit separators are not supported', line, col)
        text = self.text[start:self.i]
        value = float(text)
        if math.isinf(value):
            raise self.error('L5', f"number '{text}' is too large", line, col)
        self.add(T.NUMBER, text, value, line, col)

    def name_or_keyword(self):
        start, line, col = self.i, self.line, self.col
        while self.peek() and self.peek() in NAME_CHARS:
            self.advance()
        text = self.text[start:self.i]
        self.add(KEYWORDS.get(text, T.NAME), text, None, line, col)

    def string(self):
        line, col = self.line, self.col
        self.advance()                                       # opening quote
        start = self.i
        while not self.at_end() and self.peek() not in ('"', '\n'):
            self.advance()
        if self.at_end() or self.peek() == '\n':
            raise self.error('L6', 'unterminated string', line, col)
        value = self.text[start:self.i]
        self.advance()                                       # closing quote
        self.add(T.STRING, '"' + value + '"', value, line, col)

    def symbol(self):
        line, col = self.line, self.col
        two = self.peek() + self.peek(1)
        if two in TWO_CHAR:                                  # L3: longest match first
            self.advance(); self.advance()
            self.add(TWO_CHAR[two], two, None, line, col)
            return
        c = self.peek()
        if c in ONE_CHAR:
            self.advance()
            if c == '(':
                self.depth += 1
            elif c == ')':
                self.depth = max(0, self.depth - 1)
            self.add(ONE_CHAR[c], c, None, line, col)
            return
        hints = {'!': '; did you mean != ?', '.': '; numbers start with a digit: write 0.5',
                 '°': '; write degC or degF'}
        raise self.error('L7', f"unexpected character '{c}'" + hints.get(c, ''), line, col)


def tokenize(source: str) -> list:
    return Lexer(source).run()
