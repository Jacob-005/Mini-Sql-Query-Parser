"""A simple hand-written tokenizer for the Mini SQL language."""

import re

from lexer.token_types import Token, TokenType
from utils.error_handler import LexicalError


class SQLTokenizer:
    """Turn SQL source text into tokens while collecting lexical errors."""

    KEYWORDS = {
        token_type.name: token_type
        for token_type in (
            TokenType.SELECT,
            TokenType.FROM,
            TokenType.WHERE,
            TokenType.GROUP,
            TokenType.BY,
            TokenType.ORDER,
            TokenType.ASC,
            TokenType.DESC,
            TokenType.INSERT,
            TokenType.INTO,
            TokenType.VALUES,
            TokenType.UPDATE,
            TokenType.SET,
            TokenType.DELETE,
            TokenType.AND,
            TokenType.OR,
            TokenType.NOT,
            TokenType.NULL,
            TokenType.IS,
            TokenType.COUNT,
            TokenType.SUM,
            TokenType.AVG,
            TokenType.MIN,
            TokenType.MAX,
        )
    }

    TWO_CHARACTER_OPERATORS = {
        "!=": TokenType.NEQ,
        "<>": TokenType.NEQ,
        "<=": TokenType.LTE,
        ">=": TokenType.GTE,
    }

    ONE_CHARACTER_TOKENS = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.STAR,
        "/": TokenType.SLASH,
        "=": TokenType.EQ,
        "<": TokenType.LT,
        ">": TokenType.GT,
        ",": TokenType.COMMA,
        ".": TokenType.DOT,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        ";": TokenType.SEMICOLON,
    }

    IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*", re.ASCII)
    NUMBER_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+)?", re.ASCII)

    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.errors: list[LexicalError] = []

    def tokenize(self) -> tuple[list[Token], list[LexicalError]]:
        """Scan the complete source, returning tokens and every lexical error."""
        while not self._at_end():
            character = self._current()

            if character.isspace():
                self._advance()
            elif character == "-" and self._peek() == "-":
                self._skip_comment()
            elif character == "'":
                self._scan_string()
            elif "0" <= character <= "9":
                self._scan_number()
            elif (character.isascii() and character.isalpha()) or character == "_":
                self._scan_identifier_or_keyword()
            elif self._current_two_characters() in self.TWO_CHARACTER_OPERATORS:
                self._scan_two_character_operator()
            elif character in self.ONE_CHARACTER_TOKENS:
                self._add_token(self.ONE_CHARACTER_TOKENS[character], character)
                self._advance()
            else:
                self.errors.append(
                    LexicalError(
                        f"Invalid character '{character}'", self.line, self.column
                    )
                )
                self._advance()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens, self.errors

    def _scan_identifier_or_keyword(self) -> None:
        """Read an identifier and classify it as a keyword when appropriate."""
        start_line, start_column = self.line, self.column
        match = self.IDENTIFIER_PATTERN.match(self.source, self.index)
        if match is None:
            character = self._current()
            self.errors.append(
                LexicalError(
                    f"Invalid character '{character}'", self.line, self.column
                )
            )
            self._advance()
            return
        lexeme = match.group()
        for _ in lexeme:
            self._advance()

        token_type = self.KEYWORDS.get(lexeme.upper(), TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, lexeme, start_line, start_column))

    def _scan_number(self) -> None:
        """Read an integer or decimal, reporting numeric text with invalid suffixes."""
        start_index, start_line, start_column = self.index, self.line, self.column
        match = self.NUMBER_PATTERN.match(self.source, self.index)
        if match is None:
            character = self._current()
            self.errors.append(
                LexicalError(
                    f"Invalid character '{character}'", self.line, self.column
                )
            )
            self._advance()
            return
        valid_number = match.group()
        number_end = self.index + len(valid_number)

        if number_end < len(self.source) and (
            (self.source[number_end].isascii() and self.source[number_end].isalpha())
            or self.source[number_end] == "_"
            or self.source[number_end] == "."
        ):
            self._consume_malformed_number()
            malformed = self.source[start_index:self.index]
            self.errors.append(
                LexicalError(
                    f"Malformed number '{malformed}'", start_line, start_column
                )
            )
            return

        for _ in valid_number:
            self._advance()
        self.tokens.append(Token(TokenType.NUMBER, valid_number, start_line, start_column))

    def _consume_malformed_number(self) -> None:
        """Consume the full invalid numeric word so it creates one useful error."""
        while not self._at_end():
            character = self._current()
            if not (
                (character.isascii() and (character.isalpha() or ("0" <= character <= "9")))
                or character in "._"
            ):
                return
            self._advance()

    def _scan_string(self) -> None:
        """Read a single-quoted string, supporting doubled quotes as escapes."""
        start_index, start_line, start_column = self.index, self.line, self.column
        self._advance()  # Opening quote.

        while not self._at_end():
            if self._current() == "'":
                if self._peek() == "'":
                    self._advance()
                    self._advance()
                    continue

                self._advance()  # Closing quote.
                lexeme = self.source[start_index:self.index]
                self.tokens.append(Token(TokenType.STRING, lexeme, start_line, start_column))
                return
            self._advance()

        self.errors.append(
            LexicalError("Unterminated string", start_line, start_column)
        )

    def _scan_two_character_operator(self) -> None:
        """Add an operator that must be matched before its one-character prefix."""
        operator = self._current_two_characters()
        self._add_token(self.TWO_CHARACTER_OPERATORS[operator], operator)
        self._advance()
        self._advance()

    def _skip_comment(self) -> None:
        """Ignore a -- comment while keeping the next token's position correct."""
        while not self._at_end() and self._current() not in "\r\n":
            self._advance()

    def _add_token(self, token_type: TokenType, lexeme: str) -> None:
        """Append a token at the current source position."""
        self.tokens.append(Token(token_type, lexeme, self.line, self.column))

    def _at_end(self) -> bool:
        return self.index >= len(self.source)

    def _current(self) -> str:
        return self.source[self.index]

    def _peek(self) -> str:
        next_index = self.index + 1
        return self.source[next_index] if next_index < len(self.source) else ""

    def _current_two_characters(self) -> str:
        return self.source[self.index:self.index + 2]

    def _advance(self) -> None:
        """Move one character forward, updating 1-based line and column counters."""
        character = self.source[self.index]
        self.index += 1
        if character == "\r":
            if not self._at_end() and self._current() == "\n":
                self.index += 1
            self.line += 1
            self.column = 1
        elif character == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
