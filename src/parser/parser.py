from .ast import (
    Identifier,
    IntLiteral,
    FloatLiteral,
    TypeNode,
    VarDecl,
    BinaryExpr,
    UnaryExpr,
    FieldAccess,
)
from .operators import (
    PRIMITIVE_TYPES,
    LOGICAL_OPS,
    COMPARISON_OPS,
    ADDITIVE_OPS,
    MULTIPLICATIVE_OPS,
    UNARY_OPS,
    POSTFIX_OPS
)
from typing import Union
from src.lexer import Token, TokenType





Statement = Union[
    VarDecl, Identifier
]  # Extend this with more statement types as needed


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens: list[Token] = tokens
        self.position = 0

    # MARK:---Peek and Advance---
    def peek(self, offset=0) -> Union[Token, None]:
        if self.position + offset < len(self.tokens):
            return self.tokens[self.position + offset]
        return None

    def advance(self) -> Union[Token, None]:
        value = self.peek()
        if value is not None:
            self.position += 1
        return value

    # MARK:---Helper functions---

    def get_source_line(self, line) -> str:
        get_source_line_tokens = [
            token
            for token in self.tokens
            if token.line == line and token.type != TokenType.EOF
        ]
        if get_source_line_tokens:
            return " ".join(str(token.value) for token in get_source_line_tokens)
        return ""

    def build_error_pointer_string(self, line, column) -> str:
        source_line = self.get_source_line(line)
        return f"{source_line}\n{' ' * (column - 1)}^"

    def build_error_string(self, message, line, column) -> str:
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
                                self.peek().column,
                            )
                        )
                return TypeNode(
                    name=token.value, is_pointer=is_pointer, generic_args=generic_args
                )
            elif token_type == "primitive" and self.peek().type == TokenType.LT:
                raise SyntaxError(
                    self.build_error_string(
                        "Primitive types cannot have generic arguments",
                        self.peek().line,
                        self.peek().column,
                    )
                )
            return TypeNode(name=token.value, is_pointer=is_pointer)
        raise SyntaxError(
            self.build_error_string(
                "Unexpected type", self.peek().line, self.peek().column
            )
        )

    # MARK:---Expression parsing functions---
    def parse_expression(self) -> BinaryExpr:
        return self.parse_logical()
    
    def parse_logical(self) -> BinaryExpr:
        left = self.parse_comparision()
        while self.peek() and self.peek().type in LOGICAL_OPS:
            operator = self.peek().value
            self.advance()
            right = self.parse_comparision()
            left = BinaryExpr(left=left, operator=operator, right=right)
        return left
    
    def parse_comparision(self) -> BinaryExpr:
        left = self.parse_additive()
        while self.peek() and self.peek().type in COMPARISON_OPS:
            operator = self.peek().value
            self.advance()
            right = self.parse_additive()
            left = BinaryExpr(left=left, operator=operator, right=right)
        return left
    
    def parse_additive(self) -> BinaryExpr:
        left = self.parse_multiplicative()
        while self.peek() and self.peek().type in ADDITIVE_OPS:
            operator = self.peek().value
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryExpr(left=left, operator=operator, right=right)
        return left
    
    def parse_multiplicative(self) -> Union[BinaryExpr, UnaryExpr, IntLiteral, FloatLiteral, Identifier, FieldAccess]:
        left = self.parse_unary()
        while self.peek() and self.peek().type in MULTIPLICATIVE_OPS:
            operator = self.peek().value
            self.advance()
            right = self.parse_unary()
            left = BinaryExpr(left=left, operator=operator, right=right)
        return left
    
    def parse_unary(self) -> Union[UnaryExpr, IntLiteral, FloatLiteral, Identifier, FieldAccess]:
        if self.peek() and self.peek().type in UNARY_OPS:
            operator = self.peek().value
            self.advance()
            operand = self.parse_unary()
            return UnaryExpr(operator=operator, operand=operand)
        return self.parse_postfix()
    
    def parse_postfix(self) -> Union[UnaryExpr, IntLiteral, FloatLiteral, Identifier, FieldAccess]:
        left = self.parse_primary()
        while self.peek() and self.peek().type in POSTFIX_OPS:
            operator = self.peek().value
            self.advance()
            if operator == ".":
                if not self.peek() or self.peek().type != TokenType.IDENTIFIER:
                    raise SyntaxError(
                        self.build_error_string(
                            "Expected identifier after '.'",
                            self.peek().line,
                            self.peek().column,
                        )
                    )
                member_name = self.peek().value
                self.advance()
                left = FieldAccess(obj=left, field=member_name)
            elif operator == "(":
                raise NotImplementedError("Function call parsing not implemented yet")
            elif operator == "[":
                raise NotImplementedError("Array indexing parsing not implemented yet")
        return left

    def parse_primary(self) -> Union[IntLiteral, FloatLiteral, Identifier]:
        token = self.peek()
        match token.type:
            case TokenType.NUMBER:
                self.advance()
                if isinstance(token.value, float):
                    return FloatLiteral(value=token.value)
                return IntLiteral(value=token.value)
            case TokenType.IDENTIFIER:
                self.advance()
                return Identifier(name=token.value)
            case TokenType.LPAREN:
                self.advance()
                expr = self.parse_expression()
                if not self.peek() or self.peek().type != TokenType.RPAREN:
                    raise SyntaxError(
                        self.build_error_string(
                            "Expected ')' after expression",
                            self.peek().line,
                            self.peek().column,
                        )
                    )
                self.advance()
                return expr
            case _:
                raise SyntaxError(
                    self.build_error_string(
                        "Unexpected token in expression",
                        self.peek().line,
                        self.peek().column,
                    )
                )
    def parse_var_decl(self) -> VarDecl:
        # Expect 'const'
        is_const = False

        # Expect identifier
        if self.peek().type != TokenType.IDENTIFIER:
            raise SyntaxError(
                self.build_error_string(
                    "Expected identifier", self.peek().line, self.peek().column
                )
            )
        name = self.peek().value
        self.advance()

        # Expect ':'
        if self.peek().type != TokenType.COLON:
            raise SyntaxError(
                self.build_error_string(
                    "Expected ':'", self.peek().line, self.peek().column
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
                    "Expected '='", self.peek().line, self.peek().column
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
                            "Unexpected token", self.peek().line, self.peek().column
                        )
                    )
        return statements

    def parse_program(self) -> list[Statement]:
        try:
            return self.parse_statements()
        except SyntaxError as e:
            raise SyntaxError(f"(Syntax error):\n{e}")

    # MARK:---Entry point---
    def parse(self) -> list[Statement]:
        return self.parse_program()
