from src.lexer import TokenType

PRIMITIVE_TYPES = {
    TokenType.I8,
    TokenType.I16,
    TokenType.I32,
    TokenType.I64,
    TokenType.U8,
    TokenType.U16,
    TokenType.U32,
    TokenType.U64,
    TokenType.F32,
    TokenType.F64,
    TokenType.BOOL,
    TokenType.CHAR,
    TokenType.VOID,
}

LOGICAL_OPS = {TokenType.AND, TokenType.OR}

COMPARISON_OPS = {
    TokenType.EQEQ,
    TokenType.NE,
    TokenType.LT,
    TokenType.GT,
    TokenType.LE,
    TokenType.GE,
}

ADDITIVE_OPS = {TokenType.PLUS, TokenType.MINUS}

MULTIPLICATIVE_OPS = {TokenType.STAR, TokenType.SLASH, TokenType.MOD}

UNARY_OPS = {TokenType.MINUS, TokenType.NOT, TokenType.STAR, TokenType.AMP}

POSTFIX_OPS = {TokenType.DOT, TokenType.LPAREN, TokenType.LBRACKET}
