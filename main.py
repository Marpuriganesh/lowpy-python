from enum import Enum, auto


# ---------------- TOKEN TYPES ----------------
from enum import Enum, auto

class TokenType(Enum):
    # structure
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()

    # identifiers / literals
    IDENTIFIER = auto()
    NUMBER = auto()

    # -------- KEYWORDS --------
    CONST = auto()
    TYPE = auto()
    CLASS = auto()
    REDEF = auto()
    DEF = auto()

    RETURN = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    PUB = auto()

    IF = auto()
    ELIF = auto()
    ELSE = auto()
    MATCH = auto()

    WHILE = auto()
    FOR = auto()
    IN = auto()
    BREAK = auto()
    CONTINUE = auto()

    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    AND = auto()
    OR = auto()
    NOT = auto()
    IS = auto()

    EXTERN = auto()
    UNSAFE = auto()
    SIZEOF = auto()
    ALIGNOF = auto()
    ADDR = auto()

    # -------- TYPES --------
    I8 = auto(); I16 = auto(); I32 = auto(); I64 = auto()
    U8 = auto(); U16 = auto(); U32 = auto(); U64 = auto()
    F32 = auto(); F64 = auto()
    BOOL = auto(); CHAR = auto(); VOID = auto()
    
    STRING = auto()

    # -------- OPERATORS --------
    PLUS = auto(); MINUS = auto(); STAR = auto()
    SLASH = auto(); MOD = auto()

    EQUALS = auto()
    EQEQ = auto(); NE = auto()
    GT = auto(); LT = auto(); GE = auto(); LE = auto()

    AND_AND = auto(); OR_OR = auto()
    BANG = auto()

    AT = auto()
    ARROW = auto()
    COLON = auto()
    SEMICOLON = auto()

    DOT = auto()
    NAMESPACE = auto()
    COMMA = auto()

    LPAREN = auto(); RPAREN = auto()
    LBRACKET = auto(); RBRACKET = auto()
    LBRACE = auto(); RBRACE = auto()

    AMP = auto()

    EOF = auto()
    ERROR = auto()


KEYWORDS = {
    # keywords
    "const": TokenType.CONST,
    "type": TokenType.TYPE,
    "class": TokenType.CLASS,
    "redef": TokenType.REDEF,
    "def": TokenType.DEF,

    "return": TokenType.RETURN,
    "import": TokenType.IMPORT,
    "from": TokenType.FROM,
    "as": TokenType.AS,
    "pub": TokenType.PUB,

    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "match": TokenType.MATCH,

    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,

    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,

    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "is": TokenType.IS,

    "extern": TokenType.EXTERN,
    "unsafe": TokenType.UNSAFE,
    "sizeof": TokenType.SIZEOF,
    "alignof": TokenType.ALIGNOF,
    "addr": TokenType.ADDR,

    # primitive types
    "i8": TokenType.I8, "i16": TokenType.I16,
    "i32": TokenType.I32, "i64": TokenType.I64,

    "u8": TokenType.U8, "u16": TokenType.U16,
    "u32": TokenType.U32, "u64": TokenType.U64,

    "f32": TokenType.F32, "f64": TokenType.F64,

    "bool": TokenType.BOOL,
    "char": TokenType.CHAR,
    "void": TokenType.VOID,
}


MULTI_OPS = {
    "==": TokenType.EQEQ,
    "!=": TokenType.NE,
    ">=": TokenType.GE,
    "<=": TokenType.LE,
    "&&": TokenType.AND_AND,
    "||": TokenType.OR_OR,
    "->": TokenType.ARROW,
    "::": TokenType.NAMESPACE,
}

SINGLE_OPS = {
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.STAR,
    '/': TokenType.SLASH,
    '%': TokenType.MOD,

    '=': TokenType.EQUALS,
    '>': TokenType.GT,
    '<': TokenType.LT,

    '!': TokenType.BANG,
    '@': TokenType.AT,

    ':': TokenType.COLON,
    ';': TokenType.SEMICOLON,
    '.': TokenType.DOT,
    ',': TokenType.COMMA,

    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '[': TokenType.LBRACKET,
    ']': TokenType.RBRACKET,
    '{': TokenType.LBRACE,
    '}': TokenType.RBRACE,

    '&': TokenType.AMP,
}


ESCAPE_MAP = {
    'n': '\n',
    't': '\t',
    '\\': '\\',
    '"': '"',
    "'": "'",
    'r': '\r',  # worth adding
}

# ---------------- TOKEN ----------------
class Token:
    def __init__(self, type_, lexeme, line, column, value=None):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f"[{self.type.name}({self.value}) at {self.line}:{self.column}]"
        return f"[{self.type.name}('{self.lexeme}') at {self.line}:{self.column}]"


# ---------------- LEXER ----------------
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
    def peek(self,offset=0):
        if self.pos+offset >= len(self.source):
            return '\0'
        return self.source[self.pos + offset]


    def advance(self):
        c = self.peek()
        self.pos += 1

        if c == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return c

    # ---------- INDENTATION ----------
    def handle_indentation(self):
        count = 0
        start_col = self.column

        while self.peek() == ' ':
            self.advance()
            count += 1

        # skip empty line
        if self.peek() == '\n':
            return None

        current = self.indent_stack[-1]

        if count > current:
            self.indent_stack.append(count)
            return Token(TokenType.INDENT, "", self.line, start_col)

        elif count < current:
            tokens = []
            while count < self.indent_stack[-1]:
                self.indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, "", self.line, start_col))

            self.buffer.extend(tokens)
            return self.buffer.pop(0)

        return None

    # ---------- IDENTIFIER ----------
    def identifier(self):
        start = self.pos
        start_col = self.column

        while self.peek().isalnum() or self.peek() == '_':
            self.advance()

        text = self.source[start:self.pos]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)

        return Token(token_type, text, self.line, start_col)

    # ---------- NUMBER ----------
    def number(self):
        start = self.pos
        start_col = self.column

        value = 0
        while self.peek().isdigit():
            digit = int(self.advance())
            value = value * 10 + digit

        text = self.source[start:self.pos]
        return Token(TokenType.NUMBER, text, self.line, start_col, value=value)
    
    def handle_string_literal(self, quote_type, start_col,start_line):
        delimiter = quote_type*3 if self.peek(0) == self.peek(1) == self.peek(2) == quote_type  else quote_type
        str_val = ""
        if delimiter == quote_type*3:
            self.advance(); self.advance(); self.advance()  # consume the triple quotes
        else:
            self.advance()  # consume the opening quote
        while True:
            c = self.peek()
            if c == '\n' and delimiter != quote_type*3:
                # Unterminated string (single-line)
                return Token(TokenType.ERROR, "Unterminated string literal", self.line, start_col)
            if c == '\0':
                # Unterminated string
                return Token(TokenType.ERROR, "Unterminated string literal", self.line, start_col)
            if c == '\\':  # handle escape sequences
                self.advance()  # consume the backslash
                esc = self.peek()
                if esc in ESCAPE_MAP:
                    str_val += ESCAPE_MAP[esc]
                    self.advance()  # consume the escaped character
                else:
                    str_val += esc  # unknown escape, treat literally
                    self.advance()
            elif c == quote_type and (c == delimiter or (c+self.peek(offset=1)+self.peek(offset=2) == delimiter)):
                if len(delimiter) == 1:
                    self.advance()  # consume closing quote
                else:
                    self.advance(); self.advance(); self.advance()  # consume closing triple quotes
                break
            elif delimiter == quote_type*3 and c == quote_type and self.peek(offset=1) == quote_type and self.peek(offset=2) == quote_type:
                self.advance(); self.advance(); self.advance()  # consume closing triple quotes
                break
            else:
                str_val += c
                self.advance()
        return Token(TokenType.STRING, str_val, start_line, start_col, value=str_val)

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
        if c == '\0':
            if len(self.indent_stack) > 1:
                self.indent_stack.pop()
                return Token(TokenType.DEDENT, "", self.line, self.column)
            return Token(TokenType.EOF, "", self.line, self.column)

        # 4. NEWLINE
        if c == '\n':
            self.advance()
            self.at_line_start = True
            return Token(TokenType.NEWLINE, "\\n", self.line - 1, start_col)

        # 5. skip whitespace
        if c.isspace():
            self.advance()
            return self.next_token()

        # 6. identifiers / keywords
        if c.isalpha() or c == '_':
            return self.identifier()

        # 7. numbers
        if c.isdigit():
            return self.number()

        if c == '#':
            while self.peek() not in ('\n', '\0'):
                self.advance()
            return self.next_token()
        if c == "'" or c == '"':
            quote_type = c
            return self.handle_string_literal(quote_type, start_col,self.line)

        # 🔥 9. MULTI-CHAR OPERATORS (maximal munch)
        two = c + self.peek(offset=1)
        if two in MULTI_OPS:
            self.advance()
            self.advance()
            return Token(MULTI_OPS[two], two, self.line, start_col)

        # 🔥 10. SINGLE-CHAR OPERATORS
        if c in SINGLE_OPS:
            self.advance()
            return Token(SINGLE_OPS[c], c, self.line, start_col)

        # 11. error fallback
        self.advance()
        return Token(TokenType.ERROR, c, self.line, start_col)



code = r"""# import system
import math as m

# function definition
pub def add(x: i32, y: i32, ,z: @i32) -> i32:
    return x + y + *z
# control flow
if true and not false:
    a = 10
    b = 20
    c = a + b
elif false:
    c = 0
else:
    c = -1

# loop
for i in 10:
    if i == 5:
        break
    else:
        continue

# types and operations
x: i32 = 100
y: f64 = 3
z = x + y * 2

# namespace and arrow
result = m::sqrt(25)

#checking invalid tokens
a ::= 42

#checking string literals
s1 = "Hello, World!\n"
s2 = 'Single quoted string with a tab\tand a backslash\\'

"""
code += '\ns3 = """Triple quoted string with "quotes" and \'single quotes\' and a newline\nand a tab\tend of string"""'

code += r"""

# pointer-style ops
ptr = addr x
value = *ptr
ref = &x

# comparisons
if x >= 10 and x <= 100:
    ok = true

# comment at end
final = 42 # done
"""

def main():
    lexer = Lexer(code)
    tokens = list(lexer)
    # print(f"Tokens: {tokens}")
    indent = 0
    for tok in tokens:
        match tok.type:
            case TokenType.INDENT:
                print("    " * indent,"{" )
                indent += 1
            case TokenType.DEDENT:
                indent -= 1
                print("    " * indent,"}" ) 
            case TokenType.NEWLINE:
                print("")
            case _:
                print("    " * indent + repr(tok), end="")
    print("")
if __name__ == "__main__":
    main()