# tests/test_expressions.py

import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.parser import (
    IntLiteral,
    FloatLiteral,
    Identifier,
    BinaryExpr,
    UnaryExpr,
    FieldAccess,
)


def parse(source: str):
    lexer = Lexer(source)
    tokens =  list(lexer)
    parser = Parser(tokens)
    return parser.parse()


# MARK: --- Primary expressions ---


def test_int_literal():
    ast = parse("x: i32 = 42")
    assert isinstance(ast[0].value, IntLiteral)
    assert ast[0].value.value == 42


def test_float_literal():
    ast = parse("x: f32 = 3.14")
    assert isinstance(ast[0].value, FloatLiteral)
    assert ast[0].value.value == 3.14


def test_identifier():
    ast = parse("x: i32 = y")
    assert isinstance(ast[0].value, Identifier)
    assert ast[0].value.name == "y"


def test_grouped_expression():
    ast = parse("x: i32 = (42)")
    assert isinstance(ast[0].value, IntLiteral)
    assert ast[0].value.value == 42


# MARK: --- Binary expressions ---


def test_addition():
    ast = parse("x: i32 = 1 + 2")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "+"
    assert isinstance(expr.left, IntLiteral)
    assert isinstance(expr.right, IntLiteral)


def test_subtraction():
    ast = parse("x: i32 = 10 - 3")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "-"


def test_multiplication():
    ast = parse("x: i32 = 3 * 4")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "*"


def test_division():
    ast = parse("x: i32 = 10 / 2")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "/"


def test_modulo():
    ast = parse("x: i32 = 10 % 3")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "%"


# MARK: --- Precedence ---


def test_precedence_mul_over_add():
    ast = parse("x: i32 = 1 + 2 * 3")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "+"
    assert isinstance(expr.left, IntLiteral)
    assert isinstance(expr.right, BinaryExpr)
    assert expr.right.operator == "*"


def test_precedence_grouped():
    ast = parse("x: i32 = (1 + 2) * 3")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "*"
    assert isinstance(expr.left, BinaryExpr)
    assert expr.left.operator == "+"


def test_left_associativity():
    ast = parse("x: i32 = 1 + 2 + 3")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "+"
    assert isinstance(expr.left, BinaryExpr)  # (1+2) is left
    assert expr.left.operator == "+"
    assert isinstance(expr.right, IntLiteral)  # 3 is right


# MARK: --- Comparison ---


def test_equal():
    ast = parse("x: bool = a == b")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "=="


def test_not_equal():
    ast = parse("x: bool = a != b")
    expr = ast[0].value
    assert expr.operator == "!="


def test_less_than():
    ast = parse("x: bool = a < b")
    expr = ast[0].value
    assert expr.operator == "<"


def test_greater_than():
    ast = parse("x: bool = a > b")
    expr = ast[0].value
    assert expr.operator == ">"


# MARK: --- Logical ---


def test_logical_and():
    ast = parse("x: bool = a and b")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "and"


def test_logical_or():
    ast = parse("x: bool = a or b")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "or"


def test_logical_precedence_over_comparison():
    ast = parse("x: bool = a == b and c == d")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "and"
    assert isinstance(expr.left, BinaryExpr)
    assert expr.left.operator == "=="


# MARK: --- Unary ---


def test_unary_minus():
    ast = parse("x: i32 = -5")
    expr = ast[0].value
    assert isinstance(expr, UnaryExpr)
    assert expr.operator == "-"
    assert isinstance(expr.operand, IntLiteral)


def test_unary_not():
    ast = parse("x: bool = not a")
    expr = ast[0].value
    assert isinstance(expr, UnaryExpr)
    assert expr.operator == "not"


def test_unary_deref():
    ast = parse("x: i32 = *ptr")
    expr = ast[0].value
    assert isinstance(expr, UnaryExpr)
    assert expr.operator == "*"


def test_unary_addr_of():
    ast = parse("x: @i32 = &y")
    expr = ast[0].value
    assert isinstance(expr, UnaryExpr)
    assert expr.operator == "&"


def test_double_unary():
    ast = parse("x: i32 = - -5")
    expr = ast[0].value
    assert isinstance(expr, UnaryExpr)
    assert isinstance(expr.operand, UnaryExpr)


def test_multiply_with_deref():
    ast = parse("x: i32 = a * *b")
    expr = ast[0].value
    assert isinstance(expr, BinaryExpr)
    assert expr.operator == "*"
    assert isinstance(expr.right, UnaryExpr)
    assert expr.right.operator == "*"


# MARK: --- Field access ---


def test_field_access():
    ast = parse("x: i32 = a.b")
    expr = ast[0].value
    assert isinstance(expr, FieldAccess)
    assert expr.field == "b"
    assert isinstance(expr.obj, Identifier)


def test_grouped_field_access():
    ast = parse("x: i32 = (a).b")
    expr = ast[0].value
    assert isinstance(expr, FieldAccess)
    assert expr.field == "b"


# MARK: --- Failure cases ---


def test_fail_missing_operand():
    with pytest.raises(SyntaxError):
        parse("x: i32 = 1 +")


def test_fail_chained_pointer():
    with pytest.raises(SyntaxError):
        parse("x: @@i32 = y")


def test_fail_dot_without_identifier():
    with pytest.raises(SyntaxError):
        parse("x: i32 = a.42")


def test_fail_unclosed_paren():
    with pytest.raises(SyntaxError):
        parse("x: i32 = (1 + 2")


def test_fail_primitive_generic():
    with pytest.raises(SyntaxError):
        parse("x: i32<f32> = y")


def test_fail_unexpected_token():
    with pytest.raises(SyntaxError):
        parse("x: i32 = }")
