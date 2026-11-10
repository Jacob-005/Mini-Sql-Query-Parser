"""Error-focused checks for the shared Mini SQL analysis workflow."""

from utils.analysis import analyze_sql


def test_lexical_errors_are_all_reported_and_prevent_syntax_analysis():
    result = analyze_sql("SELECT @\nFROM t #")

    assert result.is_valid is False
    assert result.ast is None
    assert result.syntax_error is None
    assert [(error.category, error.message, error.line, error.column) for error in result.lexical_errors] == [
        ("Lexical Error", "Invalid character '@'", 1, 8),
        ("Lexical Error", "Invalid character '#'", 2, 8),
    ]
    assert [token.lexeme for token in result.tokens] == ["SELECT", "FROM", "t", ""]


def test_unterminated_string_is_a_lexical_error_with_no_ast():
    result = analyze_sql("INSERT INTO people VALUES ('Ada)")

    assert result.ast is None
    assert result.syntax_error is None
    assert result.lexical_errors[0].message == "Unterminated string"
    assert (result.lexical_errors[0].line, result.lexical_errors[0].column) == (1, 28)


def test_syntax_error_has_message_and_location_and_never_returns_an_ast():
    result = analyze_sql("SELECT *\nFROM students\nWHERE age >= ;")

    assert result.is_valid is False
    assert result.ast is None
    assert result.lexical_errors == []
    assert result.syntax_error.category == "Syntax Error"
    assert result.syntax_error.message == "Expected expression but found ';'"
    assert (result.syntax_error.line, result.syntax_error.column) == (3, 14)


def test_end_of_input_has_a_clear_syntax_message():
    result = analyze_sql("SELECT *")

    assert result.ast is None
    assert result.syntax_error.message == "Expected FROM but found end of input"
    assert (result.syntax_error.line, result.syntax_error.column) == (1, 9)


def test_unmatched_parenthesis_reports_the_missing_closer_at_end_of_input():
    result = analyze_sql("SELECT * FROM t WHERE (age = 1")

    assert result.ast is None
    assert result.syntax_error.message == "Expected ')' but found end of input"
    assert (result.syntax_error.line, result.syntax_error.column) == (1, 31)


def test_valid_multiple_statements_return_one_program_ast():
    result = analyze_sql("SELECT * FROM t; DELETE FROM t;")

    assert result.is_valid is True
    assert result.ast is not None
    assert len(result.ast.statements) == 2


def test_recursion_overflow_returns_friendly_syntax_error():
    deep_not_query = "SELECT * FROM t WHERE " + ("NOT " * 1500) + "1 = 1"
    result = analyze_sql(deep_not_query)

    assert result.is_valid is False
    assert result.ast is None
    assert result.lexical_errors == []
    assert result.syntax_error is not None
    assert result.syntax_error.message == "Query is nested too deeply"
