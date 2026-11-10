"""Error types shared by the Mini SQL Query Parser."""

from .error_handler import LexicalError, SQLSyntaxError

__all__ = ["LexicalError", "SQLSyntaxError"]
