"""One safe entry point for lexical and syntax analysis of SQL source."""

from dataclasses import dataclass

from lexer.token_types import Token
from lexer.tokenizer import SQLTokenizer
from sql_parser.ast_nodes import Program
from sql_parser.sql_parser import SQLParser
from utils.error_handler import LexicalError, SQLSyntaxError


@dataclass
class AnalysisResult:
    """The tokens and either a complete AST or friendly analysis errors."""

    tokens: list[Token]
    lexical_errors: list[LexicalError]
    syntax_error: SQLSyntaxError | None
    ast: Program | None

    @property
    def is_valid(self) -> bool:
        """True only when both analysis stages completed successfully."""
        return not self.lexical_errors and self.syntax_error is None


def analyze_sql(source: str) -> AnalysisResult:
    """Tokenize source first, then analyze only when lexical analysis succeeded."""
    tokens, lexical_errors = SQLTokenizer(source).tokenize()
    if lexical_errors:
        return AnalysisResult(tokens, lexical_errors, None, None)

    try:
        ast = SQLParser(tokens).analyze()
    except SQLSyntaxError as error:
        return AnalysisResult(tokens, [], error, None)
    except RecursionError:
        line = tokens[-1].line if tokens else 1
        column = tokens[-1].column if tokens else 1
        return AnalysisResult(
            tokens,
            [],
            SQLSyntaxError("Query is nested too deeply", line, column),
            None,
        )
    return AnalysisResult(tokens, [], None, ast)
