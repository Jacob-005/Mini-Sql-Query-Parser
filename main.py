"""Command-line entry point for the Mini SQL Query Parser."""

import argparse
import sys

from utils.analysis import AnalysisResult, analyze_sql
from visualizer.tree_visualizer import ast_to_text


def print_tokens(result: AnalysisResult) -> None:
    """Print a compact token table, including 1-based source positions."""
    print("TOKENS")
    print(f"{'TYPE':<12} {'VALUE':<20} LINE  COLUMN")
    for token in result.tokens:
        value = token.lexeme if token.lexeme else "<EOF>"
        print(f"{token.type.name:<12} {value:<20} {token.line:<5} {token.column}")


def print_result(result: AnalysisResult) -> None:
    """Print either friendly errors or the text AST for every statement."""
    print("\nANALYSIS RESULT")
    if result.is_valid:
        if result.ast is None:
            print("Unexpected internal error")
            return
        print("Valid SQL syntax.")
        for number, statement in enumerate(result.ast.statements, start=1):
            print(f"\nAST FOR STATEMENT {number}")
            print(ast_to_text(statement))
        return

    print("Invalid SQL syntax.")
    for error in result.lexical_errors:
        print(f"{error.category}: {error.message} (line {error.line}, column {error.column})")
    if result.syntax_error:
        error = result.syntax_error
        print(f"{error.category}: {error.message} (line {error.line}, column {error.column})")


def main(arguments: list[str] | None = None) -> int:
    """Analyze SQL supplied as one command-line argument and return an exit code."""
    _ensure_utf8_output()
    argument_parser = argparse.ArgumentParser(
        description="Analyze Mini SQL syntax without executing a query."
    )
    argument_parser.add_argument("sql", help="SQL query text enclosed in quotes")
    options = argument_parser.parse_args(arguments)

    try:
        result = analyze_sql(options.sql)
    except Exception:
        print("Unexpected internal error")
        return 1
    print_tokens(result)
    print_result(result)
    return 0 if result.is_valid else 1


def _ensure_utf8_output() -> None:
    """Allow the CLI to print the AST branch characters on Windows terminals."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
