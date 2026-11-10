"""Friendly error objects shown by the CLI and Streamlit UI."""

from dataclasses import dataclass


@dataclass
class SQLAnalysisError(Exception):
    """Base class for errors produced while analyzing SQL text."""

    category: str
    message: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.category}: {self.message} (line {self.line}, column {self.column})"


class LexicalError(SQLAnalysisError):
    """A character sequence cannot be converted into a valid token."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__("Lexical Error", message, line, column)


class SQLSyntaxError(SQLAnalysisError):
    """A valid token sequence does not follow the Mini SQL grammar."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__("Syntax Error", message, line, column)
