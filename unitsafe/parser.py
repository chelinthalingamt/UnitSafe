"""Parser: tokens to tree. Recursive descent, one method per grammar line
(build guide Part 3, P1-P6, D1-D3, D6, D10, D17, D19-D23)."""
from .ast_nodes import (Assign, Bool, BinOp, Call, CallStmt, Compare, FnDecl, If, KindDecl, Let,
                        Logic, Name, Neg, Not, Number, Param, Power, Print, PrintArg, Program,
                        Read, Return, String, UseDecl, UnitAnn, UnitDecl, UnitDiv, UnitLiteral, UnitMul,
                        UnitName, UnitOne, UnitPow, While)
from .errors import CompileError, ParseError
from .tokens import TokenType as T

COMPARE_OPS = (T.LT, T.GT, T.LE, T.GE, T.EQEQ, T.NOTEQ)
BLOCK_STARTS = (T.IF, T.WHILE, T.FN, T.EMPIRICAL, T.ELSE)
MAX_ERRORS = 20                                                   # D26


class _TooManyErrors(Exception):
    pass
IN_MESSAGE = "'in' is only allowed at the end of a value in print(...)"


def describe(tok) -> str:
    if tok.type == T.NEWLINE:
        return 'end of line'
    if tok.type == T.EOF:
        return 'end of file'
    return f"'{tok.text}'"


def is_integer(tok) -> bool:
    return tok.type == T.NUMBER and tok.text.isdigit()


class Parser:
    def __init__(self, tokens: list):
        self.toks = tokens
        self.i = 0
        self.errors = []                                          # D26

    # ---------- helpers ----------
    def peek(self, k: int = 0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def advance(self):
        tok = self.toks[self.i]
        if tok.type != T.EOF:
            self.i += 1
        return tok

    def check(self, *types) -> bool:
        return self.peek().type in types

    def match(self, *types):
        return self.advance() if self.check(*types) else None

    def expect(self, type_, what):
        if self.check(type_):
            return self.advance()
        if self.check(T.IN):
            raise self.error(IN_MESSAGE)
        raise self.error(f'expected {what}, found {describe(self.peek())}')

    def error(self, msg, tok=None):
        tok = tok or self.peek()
        return ParseError(CompileError('P6', tok.line, tok.col, msg))

    def pos(self, tok):
        return {'line': tok.line, 'col': tok.col}

    def skip_newlines(self):
        while self.match(T.NEWLINE):
            pass

    def end_statement(self):
        if self.check(T.EOF):
            return
        self.expect(T.NEWLINE, 'end of line')

    # ---------- program and blocks ----------
    def parse(self) -> Program:
        body = []
        self.skip_newlines()
        try:
            while not self.check(T.EOF):
                st = self.statement_or_recover()
                if st is not None:
                    body.append(st)
                self.skip_newlines()
        except _TooManyErrors:
            pass
        if self.errors:
            raise ParseError(self.errors[0], self.errors)
        return Program(body=body, line=1, col=1)

    def block(self, opener):
        stmts = []
        self.skip_newlines()
        while not self.check(T.END, T.ELSE):
            if self.check(T.EOF):
                raise self.error(f"expected 'end' to close the '{opener.text}' on line {opener.line}")
            st = self.statement_or_recover()
            if st is not None:
                stmts.append(st)
            self.skip_newlines()
        return stmts

    # ---------- D26: recovering from a syntax error ----------
    def statement_or_recover(self):
        """Parse one statement; on a syntax error record it, skip the rest of the line and
        carry on. If the error was on a line that opens a block, read that block too, so
        its 'end' is not reported as a second error."""
        try:
            st = self.statement()
            self.end_statement()
            return st
        except ParseError as e:
            self.record(e)
            first = self.first_token_on_line(e.error.line)
            self.skip_line()
            if first is not None and first.type in BLOCK_STARTS:
                self.recover_block(first)
            return None

    def record(self, e):
        self.errors.extend(e.errors)
        if len(self.errors) >= MAX_ERRORS:
            del self.errors[MAX_ERRORS:]
            raise _TooManyErrors()

    def first_token_on_line(self, line):
        for tok in self.toks:
            if tok.line == line and tok.type != T.NEWLINE:
                return tok
        return None

    def skip_line(self):
        while not self.check(T.NEWLINE, T.EOF):
            self.advance()
        self.match(T.NEWLINE)

    def recover_block(self, opener):
        try:
            self.block(opener)
            while self.match(T.ELSE):
                self.skip_line()
                self.block(opener)
            self.expect(T.END, "'end'")
            self.end_statement()
        except ParseError as e:
            self.record(e)
            self.skip_line()

    # ---------- statements ----------
    def statement(self):
        tok = self.peek()
        t = tok.type
        if t == T.UNIT:
            return self.unit_decl()
        if t == T.KIND:
            return self.kind_decl()
        if t == T.USE:
            return self.use_decl()
        if t == T.LET:
            return self.let()
        if t == T.PRINT:
            return self.print_stmt()
        if t == T.IF:
            return self.if_stmt()
        if t == T.WHILE:
            return self.while_stmt()
        if t in (T.FN, T.EMPIRICAL):
            return self.fn_decl()
        if t == T.RETURN:
            kw = self.advance()
            return Return(value=self.expression(), **self.pos(kw))
        if t == T.NAME:
            nxt = self.peek(1).type
            if nxt == T.EQUALS:
                name = self.advance()
                self.advance()
                return Assign(name=name.text, value=self.expression(), **self.pos(name))
            if nxt == T.LPAREN:                                     # D6
                call = self.call()
                return CallStmt(call=call, line=call.line, col=call.col)
            raise self.error(f"expected '=' or '(' after {tok.text}", self.peek(1))
        raise self.error(f'expected a statement, found {describe(tok)}')

    def unit_decl(self):
        kw = self.advance()
        name = self.expect(T.NAME, 'a unit name')
        number = expr = offset = kind = None
        if self.match(T.EQUALS):
            if self.check(T.NUMBER) and self.peek(1).type in (T.NAME, T.LPAREN):
                number = self.advance().value                       # conversion factor
            elif (self.check(T.MINUS) and self.peek(1).type == T.NUMBER
                  and self.peek(2).type in (T.NAME, T.LPAREN)):
                self.advance()
                number = -self.advance().value                      # refused by C3
            elif self.check(T.NUMBER) and self.peek().text != '1':
                num = self.peek()
                raise self.error(f'only the number 1 can appear inside a unit; for a conversion '
                                 f'write a unit after the number, e.g. unit {name.text} = {num.text} <unit>', num)
            expr = self.unit_expr()
            if self.match(T.OFFSET):
                offset = self.signed_number()
        if self.match(T.OF):
            kind = self.expect(T.NAME, 'a kind name').text
        return UnitDecl(name=name.text, number=number, expr=expr, offset=offset, kind=kind, **self.pos(kw))

    def signed_number(self) -> float:
        neg = self.match(T.MINUS)
        tok = self.expect(T.NUMBER, 'a number')
        return -tok.value if neg else tok.value

    def use_decl(self):                                              # D28
        kw = self.advance()
        lib = self.expect(T.NAME, "a library name after 'use'")
        self.expect(T.COLON, f"':' after use {lib.text}")
        names = []
        while True:
            tok = self.expect(T.NAME, 'a unit name')
            names.append(UnitName(name=tok.text, **self.pos(tok)))
            if not self.match(T.COMMA):
                break
        return UseDecl(lib=lib.text, names=names, **self.pos(kw))

    def kind_decl(self):
        kw = self.advance()
        name = self.expect(T.NAME, 'a kind name')
        return KindDecl(name=name.text, **self.pos(kw))

    def let(self):
        kw = self.advance()
        name = self.expect(T.NAME, 'a name after let')
        ann = self.unit_ann() if self.match(T.COLON) else None
        self.expect(T.EQUALS, "'='")
        return Let(name=name.text, ann=ann, value=self.expression(), **self.pos(kw))

    def print_stmt(self):
        kw = self.advance()
        self.expect(T.LPAREN, "'(' after print")
        args = [self.print_arg()]
        while self.match(T.COMMA):
            args.append(self.print_arg())
        self.expect(T.RPAREN, "')'")
        return Print(args=args, **self.pos(kw))

    def print_arg(self):
        start = self.peek()
        value = self.expression()
        target = self.unit_target() if self.match(T.IN) else None   # D10, D23
        return PrintArg(value=value, target=target, **self.pos(start))

    def if_stmt(self):
        kw = self.advance()
        node = self.if_rest(kw, kw)
        self.expect(T.END, f"'end' to close the 'if' on line {kw.line}")
        return node

    def if_rest(self, tok, opener):
        cond = self.expression()
        self.expect(T.NEWLINE, 'end of line')
        then = self.block(opener)
        els = None
        if self.match(T.ELSE):
            if self.check(T.IF):                                     # D21: else if
                inner = self.if_rest(self.advance(), opener)
                inner.elif_chain = True
                els = [inner]
            else:
                self.expect(T.NEWLINE, "end of line after 'else'")
                els = self.block(opener)
        return If(cond=cond, then=then, els=els, **self.pos(tok))

    def while_stmt(self):
        kw = self.advance()
        cond = self.expression()
        self.expect(T.NEWLINE, 'end of line')
        body = self.block(kw)
        self.expect(T.END, f"'end' to close the 'while' on line {kw.line}")
        return While(cond=cond, body=body, **self.pos(kw))

    def fn_decl(self):
        first = self.peek()
        empirical = bool(self.match(T.EMPIRICAL))
        if empirical and not self.check(T.FN):
            raise self.error(f"expected 'fn' after 'empirical', found {describe(self.peek())}")
        kw = self.advance()
        name = self.expect(T.NAME, 'a function name')
        self.expect(T.LPAREN, "'('")
        params = []
        if not self.check(T.RPAREN):
            params.append(self.param())
            while self.match(T.COMMA):
                params.append(self.param())
        self.expect(T.RPAREN, "')'")
        ret = self.unit_ann() if self.match(T.ARROW) else None
        self.expect(T.NEWLINE, 'end of line')
        body = self.block(kw)
        self.expect(T.END, f"'end' to close the 'fn' on line {kw.line}")
        return FnDecl(name=name.text, params=params, ret=ret, body=body, empirical=empirical,
                      **self.pos(first))

    def param(self):
        name = self.expect(T.NAME, 'a parameter name')
        ann = self.unit_ann() if self.match(T.COLON) else None
        return Param(name=name.text, ann=ann, **self.pos(name))

    # ---------- unit expressions ----------
    def unit_ann(self):
        start = self.peek()
        delta = bool(self.match(T.DELTA))
        expr = self.unit_expr()
        kind = self.expect(T.NAME, 'a kind name').text if self.match(T.OF) else None
        return UnitAnn(expr=expr, delta=delta, kind=kind, **self.pos(start))

    def unit_target(self):
        start = self.peek()
        delta = bool(self.match(T.DELTA))
        return UnitAnn(expr=self.unit_expr(), delta=delta, **self.pos(start))

    def unit_expr(self):
        left = self.unit_factor()
        while self.check(T.STAR, T.SLASH):
            op = self.advance()
            right = self.unit_factor()
            cls = UnitMul if op.type == T.STAR else UnitDiv
            left = cls(left=left, right=right, **self.pos(op))
        return left

    def unit_factor(self):
        tok = self.peek()
        if self.match(T.NAME):
            base = UnitName(name=tok.text, **self.pos(tok))
        elif self.check(T.NUMBER):
            if tok.text != '1':
                raise self.error('only the number 1 can appear inside a unit', tok)
            self.advance()
            base = UnitOne(**self.pos(tok))
        elif self.match(T.LPAREN):
            base = self.unit_expr()
            self.expect(T.RPAREN, "')'")
        else:
            raise self.error(f'expected a unit, found {describe(tok)}')
        if self.match(T.CARET):
            base = UnitPow(base=base, exp=self.int_power(), **self.pos(tok))
        return base

    def int_power(self) -> int:
        neg = self.match(T.MINUS)
        tok = self.peek()
        if not is_integer(tok):
            raise self.error('unit powers must be whole numbers', tok)
        self.advance()
        n = -int(tok.text) if neg else int(tok.text)
        if n == 0:
            raise self.error('a unit power of 0 means no unit; remove it', tok)
        return n

    # ---------- expressions ----------
    def expression(self):
        return self.or_expr()

    def or_expr(self):                                               # D20
        left = self.and_expr()
        while self.check(T.OR):
            op = self.advance()
            left = Logic(op='or', left=left, right=self.and_expr(), **self.pos(op))
        return left

    def and_expr(self):
        left = self.not_expr()
        while self.check(T.AND):
            op = self.advance()
            left = Logic(op='and', left=left, right=self.not_expr(), **self.pos(op))
        return left

    def not_expr(self):
        if self.check(T.NOT):
            op = self.advance()
            return Not(operand=self.not_expr(), **self.pos(op))
        return self.comparison()

    def comparison(self):
        left = self.sum_expr()
        if self.check(*COMPARE_OPS):
            op = self.advance()
            left = Compare(op=op.text, left=left, right=self.sum_expr(), **self.pos(op))
            if self.check(*COMPARE_OPS):
                raise self.error('only one comparison is allowed in an expression; '
                                 'write a < b and b < c')
        return left

    def sum_expr(self):
        left = self.term()
        while self.check(T.PLUS, T.MINUS):
            op = self.advance()
            left = BinOp(op=op.text, left=left, right=self.term(), **self.pos(op))
        return left

    def term(self):
        left = self.unary()
        while self.check(T.STAR, T.SLASH):
            op = self.advance()
            left = BinOp(op=op.text, left=left, right=self.unary(), **self.pos(op))
        return left

    def unary(self):                                                 # D2
        if self.check(T.MINUS):
            op = self.advance()
            return Neg(operand=self.unary(), **self.pos(op))
        return self.power()

    def power(self):                                                 # D3
        base = self.factor()
        if self.check(T.CARET):
            op = self.advance()
            if self.check(T.MINUS):
                m = self.advance()
                exp = Neg(operand=self.factor(), **self.pos(m))
            else:
                exp = self.factor()
            if self.check(T.CARET):
                raise self.error('use brackets for repeated powers: (a ^ b) ^ c')
            return Power(base=base, exp=exp, **self.pos(op))
        return base

    def factor(self):
        tok = self.peek()
        t = tok.type
        if t == T.NUMBER:
            self.advance()
            if self.check(T.NAME, T.DELTA):                          # U3: the unit sticks to its number
                return self.unit_atom(tok)
            return Number(value=tok.value, text=tok.text, **self.pos(tok))
        if t == T.STRING:
            self.advance()
            return String(value=tok.value, **self.pos(tok))
        if t == T.READ:                                              # D27
            self.advance()
            self.expect(T.LPAREN, "'(' after read")
            prompt = None
            if self.check(T.STRING):
                prompt = self.advance().value
                self.expect(T.COMMA, "',' after the prompt")
            ann = self.unit_ann()
            self.expect(T.RPAREN, "')'")
            return Read(prompt=prompt, ann=ann, **self.pos(tok))
        if t in (T.TRUE, T.FALSE):                                   # D19
            self.advance()
            return Bool(value=(t == T.TRUE), **self.pos(tok))
        if t == T.NAME:
            if self.peek(1).type == T.LPAREN:
                return self.call()
            self.advance()
            return Name(name=tok.text, **self.pos(tok))
        if t == T.LPAREN:
            self.advance()
            e = self.expression()
            self.expect(T.RPAREN, f"')' to close the '(' on line {tok.line}")
            return e
        if t == T.IN:
            raise self.error(IN_MESSAGE)
        raise self.error(f'expected a value, found {describe(tok)}')

    def unit_atom(self, num):                                        # D1, D17
        delta = bool(self.match(T.DELTA))
        name = self.expect(T.NAME, 'a unit name after delta')
        power = 1
        nxt, nxt2 = self.peek(1), self.peek(2)
        if self.check(T.CARET) and (is_integer(nxt) or (nxt.type == T.MINUS and is_integer(nxt2))):
            self.advance()
            neg = self.match(T.MINUS)
            tok = self.advance()
            power = -int(tok.text) if neg else int(tok.text)
            if power == 0:
                raise self.error('a unit power of 0 means no unit; remove it', tok)
        return UnitLiteral(value=num.value, text=num.text, unit=name.text, power=power,
                           delta=delta, **self.pos(num))

    def call(self):
        name = self.advance()
        open_ = self.advance()                                       # '('
        args = []
        if not self.check(T.RPAREN):
            args.append(self.expression())
            while self.match(T.COMMA):
                args.append(self.expression())
        self.expect(T.RPAREN, f"')' to close the '(' on line {open_.line}")
        return Call(name=name.text, args=args, **self.pos(name))


def parse(tokens: list) -> Program:
    return Parser(tokens).parse()
