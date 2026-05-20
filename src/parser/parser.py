from .ast import Identifier, IntLiteral, FloatLiteral, TypeNode, VarDecl
from src.lexer import TokenType, Token
from typing import Union

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

Statement = Union[VarDecl,Identifier]  # Extend this with more statement types as needed


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens: list[Token] = tokens
        self.position = 0


    # MARK:---Peek and Advance---
    def peek(self, offset=0)-> Union[Token, None]:
        if self.position + offset < len(self.tokens):
            return self.tokens[self.position + offset]
        return None

    def advance(self)-> Union[Token, None]:
        value = self.peek()
        if value is not None:
            self.position += 1
        return value

    # MARK:---Helper functions---

    def get_source_line(self, line)-> str:
        get_source_line_tokens = [token for token in self.tokens if token.line == line and token.type != TokenType.EOF]
        if get_source_line_tokens:
            return " ".join(str(token.value )for token in get_source_line_tokens)
        return ""

    def build_error_pointer_string(self, line, column)-> str:
        source_line = self.get_source_line(line)
        return f"{source_line}\n{' ' * (column - 1)}^"
    
    def build_error_string(self, message, line, column)-> str:
        pointer_string = self.build_error_pointer_string(line, column)
        return f"{pointer_string}\n{message} at line {line}, column {column}"

    # MARK:---Parsing functions---

    def parse_type(self) -> TypeNode:
        token = self.peek()
        token_type = None
        is_pointer = False
        
        if token.type == TokenType.AT:
            self.advance()  # consume '@'
            is_pointer = True
            token = self.peek()  # update token to the next one after '@'
            if token.type == TokenType.AT:
                raise SyntaxError(
                    self.build_error_string(
                        "Pointer types cannot be chained — '@' cannot follow '@'",
                        token.line,
                        token.column,
                    )
                )
        
        if token.type in PRIMITIVE_TYPES or token.type == TokenType.IDENTIFIER:
            if token.type in PRIMITIVE_TYPES:
                token_type = "primitive"
            else:
                token_type = "identifier"
            self.advance()
            if token_type == "identifier" and self.peek().type == TokenType.LT:
                self.advance()  # consume '<'
                generic_args = []
                while True:
                    generic_args.append(self.parse_type())
                    if self.peek().type == TokenType.COMMA:
                        self.advance()  # consume ','
                    elif self.peek().type == TokenType.GT:
                        self.advance()  # consume '>'
                        break
                    else:
                        raise SyntaxError(
                            self.build_error_string(
                                "Expected ',' or '>' in generic type",
                                self.peek().line,
                                self.peek().column
                            )
                        )
                return TypeNode(name=token.value, is_pointer=is_pointer, generic_args=generic_args)
            elif token_type == "primitive" and self.peek().type == TokenType.LT:
                raise SyntaxError(
                    self.build_error_string(
                        "Primitive types cannot have generic arguments",
                        self.peek().line,
                        self.peek().column
                    )
                )
            return TypeNode(name=token.value, is_pointer=is_pointer)
        raise SyntaxError(self.build_error_string("Unexpected type", self.peek().line, self.peek().column))

    def parse_expression(self) -> IntLiteral | FloatLiteral | Identifier:
        # Placeholder for expression parsing logic
        token = self.peek()
        if token.type == TokenType.NUMBER:
            self.advance()
            if isinstance(token.value, float):
                return FloatLiteral(value=token.value)
            return IntLiteral(value=token.value)

        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(name=token.value)
        else:
            raise SyntaxError(
                self.build_error_string(
                    "Unexpected token in expression",
                    self.peek().line,
                    self.peek().column
                )
            )

    def parse_var_decl(self) -> VarDecl:
        # Expect 'const'
        is_const = False

        # Expect identifier
        if self.peek().type != TokenType.IDENTIFIER:
            raise SyntaxError(
                self.build_error_string(
                    "Expected identifier",
                    self.peek().line,
                    self.peek().column
                )
            )
        name = self.peek().value
        self.advance()

        # Expect ':'
        if self.peek().type != TokenType.COLON:
            raise SyntaxError(
                self.build_error_string(
                    "Expected ':'",
                    self.peek().line,
                    self.peek().column
                )
            )
        self.advance()

        if self.peek().type == TokenType.CONST:
            is_const = True
            self.advance()

        # Parse type
        type_node = self.parse_type()

        # Expect '='
        if self.peek().type != TokenType.EQUALS:
            raise SyntaxError(
                self.build_error_string(
                    "Expected '='",
                    self.peek().line,
                    self.peek().column
                )
            )
        self.advance()

        # Parse expression
        value = self.parse_expression()

        return VarDecl(name=name, type=type_node, value=value, is_const=is_const)

    def parse_statements(self) -> list[Statement]:
        statements = []
        # Placeholder for statement parsing logic
        while self.peek() is not None:
            match self.peek().type:
                case TokenType.IDENTIFIER:
                    statements.append(self.parse_var_decl())
                case TokenType.DEF:
                    statements.append(self.parse_function_decl())
                case TokenType.NEWLINE:
                    self.advance()
                case TokenType.EOF:
                    break
                case _:
                    raise SyntaxError(
                        self.build_error_string(
                            "Unexpected token",
                            self.peek().line,
                            self.peek().column
                        )
                    )
        return statements

    def parse_program(self) -> list[Statement]:
        try:
            return self.parse_statements()
        except SyntaxError as e:
            raise SyntaxError(f"(Syntax error):\n{e}")
    # MARK:---Entry point---
    def parse(self)-> list[Statement]:
        return self.parse_program()
