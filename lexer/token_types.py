"""Token definitions used by the handwritten SQL tokenizer."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Every token recognized by the Mini SQL language."""

    # SQL keywords.  Each keyword has its own type so grammar rules stay clear.
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    GROUP = auto()
    BY = auto()
    ORDER = auto()
    ASC = auto()
    DESC = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    NULL = auto()
    IS = auto()
    COUNT = auto()
    SUM = auto()
    AVG = auto()
    MIN = auto()
    MAX = auto()

    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()

    COMMA = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    """A lexical token and the 1-based location where it starts."""

    type: TokenType
    lexeme: str
    line: int
    column: int
