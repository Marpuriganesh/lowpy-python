from enum import Enum, auto


# MARK: TOKEN TYPES ----------------
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
    I8 = auto()
    I16 = auto()
    I32 = auto()
    I64 = auto()

    U8 = auto()
    U16 = auto()
    U32 = auto()
    U64 = auto()

    F32 = auto()
    F64 = auto()

    BOOL = auto()
    CHAR = auto()
    VOID = auto()

    STRING = auto()
    WIDE_STRING = auto()
    FORMATTED_STRING = auto()

    # -------- OPERATORS --------
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    MOD = auto()

    EQUALS = auto()
    EQEQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()

    AND_AND = auto()
    OR_OR = auto()
    BANG = auto()

    AT = auto()
    ARROW = auto()
    COLON = auto()
    SEMICOLON = auto()

    DOT = auto()
    NAMESPACE = auto()
    COMMA = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()

    AMP = auto()

    # ------ Complier Dunder Methods ------
    DUNDER_INIT = auto()
    DUNDER_NEW = auto()
    DUNDER_DEL = auto()
    DUNDER_STR = auto()
    DUNDER_REPR = auto()
    DUNDER_ADD = auto()
    DUNDER_SUB = auto()
    DUNDER_MUL = auto()
    DUNDER_DIV = auto()
    DUNDER_EQ = auto()
    DUNDER_LT = auto()
    DUNDER_LEN = auto()
    DUNDER_GETITEM = auto()
    DUNDER_TYPE_LAYOUT = auto()

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
    "i8": TokenType.I8,
    "i16": TokenType.I16,
    "i32": TokenType.I32,
    "i64": TokenType.I64,
    "u8": TokenType.U8,
    "u16": TokenType.U16,
    "u32": TokenType.U32,
    "u64": TokenType.U64,
    "f32": TokenType.F32,
    "f64": TokenType.F64,
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
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.MOD,
    "=": TokenType.EQUALS,
    ">": TokenType.GT,
    "<": TokenType.LT,
    "!": TokenType.BANG,
    "@": TokenType.AT,
    ":": TokenType.COLON,
    ";": TokenType.SEMICOLON,
    ".": TokenType.DOT,
    ",": TokenType.COMMA,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "&": TokenType.AMP,
}

DUNDER_KEYWORDS = {
    "__init__": TokenType.DUNDER_INIT,
    "__new__": TokenType.DUNDER_NEW,
    "__del__": TokenType.DUNDER_DEL,
    "__str__": TokenType.DUNDER_STR,
    "__repr__": TokenType.DUNDER_REPR,
    "__add__": TokenType.DUNDER_ADD,
    "__sub__": TokenType.DUNDER_SUB,
    "__mul__": TokenType.DUNDER_MUL,
    "__div__": TokenType.DUNDER_DIV,
    "__eq__": TokenType.DUNDER_EQ,
    "__lt__": TokenType.DUNDER_LT,
    "__len__": TokenType.DUNDER_LEN,
    "__getitem__": TokenType.DUNDER_GETITEM,
    "__layout__": TokenType.DUNDER_TYPE_LAYOUT,
}


ESCAPE_MAP = {
    "n": "\n",
    "t": "\t",
    "\\": "\\",
    '"': '"',
    "'": "'",
    "r": "\r",  # worth adding
}
