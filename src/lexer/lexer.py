from .keywords import (
    KEYWORDS,
    DUNDER_KEYWORDS,
    TokenType,
    MULTI_OPS,
    SINGLE_OPS,
    ESCAPE_MAP,
)


# MARK: TOKEN ----------------
class Token:
    def __init__(self, type_, lexeme, line, column, value=None):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.value = value

    def to_dict(self):
        return {
            "type": self.type.name,
            "lexeme": self.lexeme,
            "line": self.line,
            "column": self.column,
            "value": self.value,
        }

    def __repr__(self):
        if self.value is not None:
            return f"[{self.type.name}({self.value}) at {self.line}:{self.column}]"
        return f"[{self.type.name}('{self.lexeme}') at {self.line}:{self.column}]"


# MARK: LEXER ----------------
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

        # indentation
        self.indent_stack = [0]
        self.at_line_start = True

        # buffered tokens (DEDENT bursts, etc.)
        self.buffer = []

        self.finished = False  # for iterator

    # ---------- ITERATOR INTERFACE ----------
    def __iter__(self):
        return self

    def __next__(self):
        if self.finished:
            raise StopIteration

        tok = self.next_token()

        if tok.type == TokenType.EOF:
            self.finished = True
            return tok  # include EOF once

        return tok

    # ---------- CORE UTILS ----------
    def peek(self, offset=0):
        if self.pos + offset >= len(self.source):
            return "\0"
        return self.source[self.pos + offset]

    def advance(self):
        c = self.peek()
        self.pos += 1

        if c == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return c

    # ---------- INDENTATION ----------
    def handle_indentation(self):
        indent_char = None
        count = 0
        start_col = self.column

        while self.peek() in (" ", "\t"):
            c = self.peek()
            if indent_char is None:
                indent_char = c
            elif c != indent_char:
                return Token(
                    TokenType.ERROR,
                    "Mixed tabs and spaces in indentation",
                    self.line,
                    self.column,
                )
            if c == "\t":
                count += 8
            else:
                count += 1
            self.advance()

        # skip empty line
        if self.peek() == "\n":
            return None

        current = self.indent_stack[-1]

        if count > current:
            self.indent_stack.append(count)
            return Token(TokenType.INDENT, "", self.line, start_col, value="INDENT")

        elif count < current:
            tokens = []
            while count < self.indent_stack[-1]:
                self.indent_stack.pop()
                tokens.append(
                    Token(TokenType.DEDENT, "", self.line, start_col, value="DEDENT")
                )

            self.buffer.extend(tokens)
            return self.buffer.pop(0)

        return None

    # ---------- IDENTIFIER ----------
    def identifier(self):
        start = self.pos
        start_col = self.column

        while self.peek().isalnum() or self.peek() == "_":
            self.advance()

        text = self.source[start : self.pos]
        token_type = KEYWORDS.get(text, DUNDER_KEYWORDS.get(text, TokenType.IDENTIFIER))

        return Token(token_type, text, self.line, start_col, value=text)

    # ---------- NUMBER ----------
    def number(self):
        start = self.pos
        start_col = self.column

        value = 0
        fraction_part = 0.0
        exponent_part = 0

        while self.peek().isdigit() or (self.peek() == "_" and self.peek(1).isdigit()):
            if self.peek() == "_":
                self.advance()  # skip underscore
                continue
            digit = int(self.advance())
            value = value * 10 + digit

        if self.peek() == "." and self.peek(1).isdigit():
            self.advance()
            fraction_part_count = 0
            while self.peek().isdigit() or (
                self.peek() == "_" and self.peek(1).isdigit()
            ):
                if self.peek() == "_":
                    self.advance()
                    continue
                digit = int(self.advance())
                fraction_part = fraction_part + (
                    digit / 10 ** (fraction_part_count + 1)
                )
                fraction_part_count += 1

        value += fraction_part if fraction_part else 0

        if self.peek() in ("e", "E") and (
            self.peek(1).isdigit()
            or (self.peek(1) in ("+", "-") and self.peek(2).isdigit())
        ):
            sign = 1
            self.advance()
            if self.peek() in ("+", "-"):
                sign = 1 if self.advance() == "+" else -1
            while self.peek().isdigit() or (
                self.peek() == "_" and self.peek(1).isdigit()
            ):
                if self.peek() == "_":
                    self.advance()
                    continue
                digit = int(self.advance())
                exponent_part = exponent_part * 10 + digit
            exponent_part *= sign

        value = value * (10**exponent_part)

        text = self.source[start : self.pos]
        return Token(TokenType.NUMBER, text, self.line, start_col, value=value)

    def handle_string_literal(self, quote_type, start_col, start_line, prefix=None):
        str_val = ""
        skip_escape = False
        string_type = TokenType.STRING

        if prefix:
            match prefix:
                case "r":
                    skip_escape = True
                case "f":
                    return Token(
                        TokenType.ERROR,
                        "f-strings are not supported for static allocation it should be used with an allocator",
                        start_line,
                        start_col,
                        value="f-strings are not supported for static allocation it should be used with an allocator",
                    )
                case "u":
                    string_type = TokenType.WIDE_STRING
                case _:
                    return Token(
                        TokenType.ERROR,
                        f"Unknown string prefix {prefix}",
                        start_line,
                        start_col,
                        value=f"Unknown string prefix {prefix}",
                    )

        # 🔥 Step 1: detect triple or single
        if (
            self.peek() == quote_type
            and self.peek(1) == quote_type
            and self.peek(2) == quote_type
        ):
            delimiter = quote_type * 3
            self.advance()
            self.advance()
            self.advance()
        else:
            delimiter = quote_type
            self.advance()

        # 🔥 Step 2: read content
        while True:
            c = self.peek()

            # EOF
            if c == "\0":
                return Token(
                    TokenType.ERROR,
                    "Unterminated string literal",
                    start_line,
                    start_col,
                    value="Unterminated string literal",
                )

            # Single-line string cannot span newline
            if delimiter == quote_type and c == "\n":
                return Token(
                    TokenType.ERROR,
                    "Unterminated string literal",
                    start_line,
                    start_col,
                    value="Unterminated string literal",
                )

            # Escape handling
            if c == "\\" and not skip_escape:
                self.advance()
                esc = self.peek()

                if esc in ESCAPE_MAP:
                    str_val += ESCAPE_MAP[esc]
                    self.advance()
                else:
                    return Token(
                        TokenType.ERROR,
                        f"Invalid escape \\{esc}",
                        self.line,
                        self.column,
                        value=f"Invalid escape \\{esc}",
                    )

                continue

            # 🔥 Closing delimiter
            if delimiter == quote_type:
                if c == quote_type:
                    self.advance()
                    break
            else:
                if (
                    self.peek() == quote_type
                    and self.peek(1) == quote_type
                    and self.peek(2) == quote_type
                ):
                    self.advance()
                    self.advance()
                    self.advance()
                    break

            # Normal char
            str_val += c
            self.advance()

        return Token(string_type, str_val, start_line, start_col, value=str_val)

    # ---------- MAIN ENGINE ----------
    def next_token(self):
        # 1. buffered tokens first
        if self.buffer:
            return self.buffer.pop(0)

        # 2. indentation
        if self.at_line_start:
            self.at_line_start = False
            tok = self.handle_indentation()
            if tok:
                return tok

        c = self.peek()
        start_col = self.column

        # 3. EOF handling
        if c == "\0":
            if len(self.indent_stack) > 1:
                self.indent_stack.pop()
                return Token(
                    TokenType.DEDENT, "", self.line, self.column, value="DEDENT"
                )
            return Token(TokenType.EOF, "", self.line, self.column, value="EOF")

        # 4. NEWLINE
        if c == "\n":
            self.advance()
            self.at_line_start = True
            return Token(
                TokenType.NEWLINE, "\\n", self.line - 1, start_col, value="NEWLINE"
            )

        # 5. skip whitespace
        if c.isspace():
            self.advance()
            return self.next_token()

        if c.isalpha() and (self.peek(1) == '"' or self.peek(1) == "'"):
            prefix = c
            quote_type = self.peek(1)
            self.advance()  # consume prefix
            return self.handle_string_literal(
                quote_type, start_col, self.line, prefix=prefix
            )

        # 6. identifiers / keywords
        if c.isalpha() or c == "_":
            return self.identifier()

        # 7. numbers
        if c.isdigit():
            return self.number()

        if c == "#":
            while self.peek() not in ("\n", "\0"):
                self.advance()
            return self.next_token()

        if c == "'" or c == '"':
            quote_type = c
            return self.handle_string_literal(quote_type, start_col, self.line)

        # 🔥 9. MULTI-CHAR OPERATORS (maximal munch)
        two = c + self.peek(offset=1)
        if two in MULTI_OPS:
            self.advance()
            self.advance()
            return Token(MULTI_OPS[two], two, self.line, start_col, value=two)

        # 🔥 10. SINGLE-CHAR OPERATORS
        if c in SINGLE_OPS:
            self.advance()
            return Token(SINGLE_OPS[c], c, self.line, start_col, value=c)

        # 11. error fallback
        self.advance()
        return Token(
            TokenType.ERROR, c, self.line, start_col, value=f"Unknown character: {c}"
        )
