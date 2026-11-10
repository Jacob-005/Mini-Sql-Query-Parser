"""Unit tests for the recursive-descent Mini SQL analyzer."""

import pytest

from lexer.tokenizer import SQLTokenizer
from sql_parser.ast_nodes import (
    Aggregate,
    BinaryOp,
    DeleteStatement,
    InsertStatement,
    IsNull,
    SelectStatement,
    UnaryOp,
    UpdateStatement,
)
from sql_parser.sql_parser import SQLParser
from utils.analysis import analyze_sql
from utils.error_handler import SQLSyntaxError


def analyze(source: str):
    """Tokenize valid source and build its program AST for each test."""
    tokens, errors = SQLTokenizer(source).tokenize()
    assert errors == []
    return SQLParser(tokens).analyze()


def test_select_with_all_optional_clauses():
    program = analyze(
        "SELECT department, COUNT(*) FROM staff WHERE age >= 18 "
        "GROUP BY department ORDER BY department DESC"
    )
    statement = program.statements[0]

    assert isinstance(statement, SelectStatement)
    assert statement.table.name == "staff"
    assert isinstance(statement.select_items[1], Aggregate)
    assert statement.where.condition.operator == ">="
    assert [column.name for column in statement.group_by.columns] == ["department"]
    assert statement.order_by.items[0].direction == "DESC"


def test_insert_with_columns_multiple_rows_negative_decimals_and_strings():
    program = analyze(
        "INSERT INTO scores (name, mark, note) VALUES "
        "('Ada Lovelace', -12.5, 'it''s ready'), ('Lin', 18, NULL)"
    )
    statement = program.statements[0]

    assert isinstance(statement, InsertStatement)
    assert [column.name for column in statement.columns] == ["name", "mark", "note"]
    assert len(statement.rows) == 2
    assert statement.rows[0].values[1].value == "-12.5"
    assert statement.rows[0].values[2].value == "it's ready"
    assert statement.rows[1].values[2].kind == "null"


def test_update_with_multiple_assignments_and_where_clause():
    program = analyze("UPDATE students SET age = 21, score = score + 1 WHERE name IS NOT NULL")
    statement = program.statements[0]

    assert isinstance(statement, UpdateStatement)
    assert len(statement.assignments) == 2
    assert isinstance(statement.assignments[1].value, BinaryOp)
    assert isinstance(statement.where.condition, IsNull)
    assert statement.where.condition.is_not is True


def test_delete_with_where_clause():
    program = analyze("DELETE FROM logs WHERE created_at < 10")
    statement = program.statements[0]

    assert isinstance(statement, DeleteStatement)
    assert statement.table.name == "logs"
    assert statement.where.condition.operator == "<"


def test_keywords_are_case_insensitive_in_every_statement_type():
    program = analyze("sElEcT * fRoM people; InSeRt InTo tags VaLuEs (1); dElEtE FrOm tags")

    assert [type(statement) for statement in program.statements] == [
        SelectStatement,
        InsertStatement,
        DeleteStatement,
    ]


def test_expression_precedence_and_left_associativity():
    program = analyze("SELECT * FROM t WHERE a = 1 OR b = 2 AND c = 3 OR d = 4")
    root = program.statements[0].where.condition

    assert isinstance(root, BinaryOp)
    assert root.operator == "OR"
    assert isinstance(root.left, BinaryOp)
    assert root.left.operator == "OR"
    assert isinstance(root.left.right, BinaryOp)
    assert root.left.right.operator == "AND"


def test_unary_not_negative_values_and_parentheses():
    program = analyze("SELECT * FROM t WHERE NOT (price + 2 * -3) >= 10")
    condition = program.statements[0].where.condition

    assert isinstance(condition, UnaryOp)
    assert condition.operator == "NOT"
    assert isinstance(condition.operand, BinaryOp)
    assert condition.operand.operator == ">="


def test_count_and_expression_aggregate_arguments():
    program = analyze("SELECT COUNT(*), SUM(price + tax), AVG(score), MIN(x), MAX(y) FROM t")
    items = program.statements[0].select_items

    assert [item.function for item in items] == ["COUNT", "SUM", "AVG", "MIN", "MAX"]
    assert items[0].argument is None
    assert isinstance(items[1].argument, BinaryOp)


def test_is_null_and_not_null_conditions():
    program = analyze("SELECT * FROM t WHERE a IS NULL OR b IS NOT NULL")
    root = program.statements[0].where.condition

    assert isinstance(root.left, IsNull) and root.left.is_not is False
    assert isinstance(root.right, IsNull) and root.right.is_not is True


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("SELECT name students;", "Expected FROM but found 'students'"),
        ("SELECT FROM students;", "Expected expression but found 'FROM'"),
        ("INSERT students VALUES (1, 'A');", "Expected INTO but found 'students'"),
        ("UPDATE students age = 21;", "Expected SET but found 'age'"),
        ("DELETE students;", "Expected FROM but found 'students'"),
        ("SELECT name FROM students WHERE age >= ;", "Expected expression but found ';'"),
        ("SELECT (name FROM students", "Expected ')' but found 'FROM'"),
        ("SELECT a,, b FROM t", "Expected expression but found ','"),
        ("SELECT a, FROM t", "Expected expression but found 'FROM'"),
        ("SELECT * FROM t; abc", "Expected SELECT, INSERT, UPDATE, or DELETE but found 'abc'"),
    ],
)
def test_common_syntax_errors_have_friendly_messages(source: str, message: str):
    tokens, errors = SQLTokenizer(source).tokenize()
    assert errors == []

    with pytest.raises(SQLSyntaxError) as caught:
        SQLParser(tokens).analyze()

    assert caught.value.category == "Syntax Error"
    assert caught.value.message == message


def test_expected_identifier_mentions_reserved_keyword_when_found():
    tokens, errors = SQLTokenizer("SELECT * FROM SELECT").tokenize()
    assert errors == []

    with pytest.raises(SQLSyntaxError) as caught:
        SQLParser(tokens).analyze()

    assert caught.value.message == "Expected identifier but found reserved keyword 'select'"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("SELECT COUNT 1 FROM t", "Expected '(' but found '1'"),
        ("UPDATE t SET a 1", "Expected '=' but found '1'"),
        ("SELECT * FROM t SELECT * FROM u", "Expected ';' or end of input but found 'SELECT'"),
        ("SELECT * FROM 123", "Expected identifier but found '123'"),
    ],
)
def test_expected_messages_use_symbols_for_common_tokens(source: str, message: str):
    tokens, errors = SQLTokenizer(source).tokenize()
    assert errors == []

    with pytest.raises(SQLSyntaxError) as caught:
        SQLParser(tokens).analyze()

    assert caught.value.message == message


def test_deeply_nested_parentheses_return_friendly_depth_error():
    nested_expression = "(" * 150 + "1" + ")" * 150
    result = analyze_sql(f"SELECT * FROM t WHERE {nested_expression}")

    assert result.ast is None
    assert result.syntax_error is not None
    assert result.syntax_error.message == "Query is nested too deeply"


def test_optional_semicolon_and_multiple_statements_are_accepted():
    program = analyze("SELECT * FROM t; DELETE FROM t WHERE id = 1;")

    assert len(program.statements) == 2
