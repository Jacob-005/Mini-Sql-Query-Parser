"""Unit tests for the handwritten Mini SQL tokenizer."""

import pytest

from lexer.token_types import TokenType
from lexer.tokenizer import SQLTokenizer


def tokenize(source: str):
    """Make test assertions concise by tokenizing one source string."""
    return SQLTokenizer(source).tokenize()


def token_types(source: str) -> list[TokenType]:
    """Return just token types, including the mandatory EOF token."""
    tokens, errors = tokenize(source)
    assert errors == []
    return [token.type for token in tokens]


def test_keywords_are_case_insensitive_and_keep_original_spelling():
    tokens, errors = tokenize("select FrOm students WHERE age > 20")

    assert errors == []
    assert [token.type for token in tokens] == [
        TokenType.SELECT,
        TokenType.FROM,
        TokenType.IDENTIFIER,
        TokenType.WHERE,
        TokenType.IDENTIFIER,
        TokenType.GT,
        TokenType.NUMBER,
        TokenType.EOF,
    ]
    assert [token.lexeme for token in tokens[:2]] == ["select", "FrOm"]


def test_identifiers_allow_underscores_and_digits_after_the_first_character():
    tokens, errors = tokenize("SELECT student_2, _status FROM class_10")

    assert errors == []
    assert [token.lexeme for token in tokens] == [
        "SELECT", "student_2", ",", "_status", "FROM", "class_10", ""
    ]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("1", [TokenType.NUMBER, TokenType.EOF]),
        ("12.50", [TokenType.NUMBER, TokenType.EOF]),
        ("-42", [TokenType.MINUS, TokenType.NUMBER, TokenType.EOF]),
    ],
)
def test_number_tokens(source: str, expected: list[TokenType]):
    assert token_types(source) == expected


def test_strings_keep_spaces_and_escaped_quotes():
    tokens, errors = tokenize("'Ada Lovelace''s note'")

    assert errors == []
    assert tokens[0].type is TokenType.STRING
    assert tokens[0].lexeme == "'Ada Lovelace''s note'"


def test_longest_two_character_operators_are_recognized_first():
    assert token_types("a != b <> c <= d >= e") == [
        TokenType.IDENTIFIER,
        TokenType.NEQ,
        TokenType.IDENTIFIER,
        TokenType.NEQ,
        TokenType.IDENTIFIER,
        TokenType.LTE,
        TokenType.IDENTIFIER,
        TokenType.GTE,
        TokenType.IDENTIFIER,
        TokenType.EOF,
    ]


def test_punctuation_and_single_character_operators():
    assert token_types("+,*/=< >.();") == [
        TokenType.PLUS,
        TokenType.COMMA,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.EQ,
        TokenType.LT,
        TokenType.GT,
        TokenType.DOT,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]


def test_comments_and_whitespace_are_skipped_with_correct_locations():
    tokens, errors = tokenize("SELECT\n-- ignore this\n  name FROM students")

    assert errors == []
    assert [(token.lexeme, token.line, token.column) for token in tokens] == [
        ("SELECT", 1, 1),
        ("name", 3, 3),
        ("FROM", 3, 8),
        ("students", 3, 13),
        ("", 3, 21),
    ]


def test_windows_newlines_count_as_one_new_line():
    tokens, errors = tokenize("SELECT\r\nname")

    assert errors == []
    assert (tokens[1].line, tokens[1].column) == (2, 1)


def test_invalid_characters_are_all_collected_and_scanning_continues():
    tokens, errors = tokenize("SELECT @ name # FROM students")

    assert [token.lexeme for token in tokens] == ["SELECT", "name", "FROM", "students", ""]
    assert [(error.message, error.line, error.column) for error in errors] == [
        ("Invalid character '@'", 1, 8),
        ("Invalid character '#'", 1, 15),
    ]


@pytest.mark.parametrize("source", ["1.2.3", "12abc", "2_value"])
def test_malformed_numbers_are_reported(source: str):
    tokens, errors = tokenize(source)

    assert [token.type for token in tokens] == [TokenType.EOF]
    assert len(errors) == 1
    assert errors[0].category == "Lexical Error"
    assert errors[0].message == f"Malformed number '{source}'"
    assert (errors[0].line, errors[0].column) == (1, 1)


def test_unterminated_string_is_reported_at_the_opening_quote():
    tokens, errors = tokenize("SELECT 'missing")

    assert [token.lexeme for token in tokens] == ["SELECT", ""]
    assert len(errors) == 1
    assert errors[0].message == "Unterminated string"
    assert (errors[0].line, errors[0].column) == (1, 8)


@pytest.mark.parametrize(
    ("source", "bad_character", "column"),
    [
        ("SELECT é FROM t", "é", 8),
        ("SELECT ² FROM t", "²", 8),
    ],
)
def test_non_ascii_characters_are_reported_as_invalid(source: str, bad_character: str, column: int):
    tokens, errors = tokenize(source)

    assert [token.lexeme for token in tokens] == ["SELECT", "FROM", "t", ""]
    assert len(errors) == 1
    assert errors[0].message == f"Invalid character '{bad_character}'"
    assert (errors[0].line, errors[0].column) == (1, column)
