"""Tests for the command-line Mini SQL interface."""

from main import main


def test_cli_prints_tokens_result_and_tree_for_valid_sql(capsys):
    exit_code = main(["SELECT * FROM students;"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "TOKENS" in output
    assert "SELECT" in output
    assert "Valid SQL syntax." in output
    assert "AST FOR STATEMENT 1" in output
    assert "SELECT *" in output


def test_cli_prints_a_friendly_error_for_invalid_sql(capsys):
    exit_code = main(["SELECT name students;"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Invalid SQL syntax." in output
    assert "Syntax Error: Expected FROM but found 'students'" in output
