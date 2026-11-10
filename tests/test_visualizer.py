"""Tests for generic text and Graphviz DOT AST rendering."""

from lexer.tokenizer import SQLTokenizer
from sql_parser.sql_parser import SQLParser
from visualizer.tree_visualizer import ast_to_dot, ast_to_text


def make_ast(source: str):
    """Build a valid AST for visualizer tests."""
    tokens, errors = SQLTokenizer(source).tokenize()
    assert errors == []
    return SQLParser(tokens).analyze()


def test_text_tree_has_branch_characters_and_operator_precedence():
    ast = make_ast("SELECT * FROM t WHERE a = 1 OR b = 2 AND c = 3")
    tree = ast_to_text(ast)

    assert tree.startswith("Program\n└── SELECT *")
    assert "└── Binary: OR" in tree
    assert tree.index("Binary: OR") < tree.index("Binary: AND")
    assert "Column: c" in tree


def test_dot_graph_contains_nodes_and_edges_for_the_ast():
    ast = make_ast("INSERT INTO t VALUES ('Ada')")
    dot = ast_to_dot(ast)

    assert dot.startswith("digraph AST {")
    assert 'node_0 [label="Program"]' in dot
    assert 'label="String: Ada"' in dot
    assert "node_0 -> node_1;" in dot
    assert dot.endswith("}")


def test_dot_graph_escapes_special_characters_in_labels():
    ast = make_ast("INSERT INTO t VALUES ('Ada said \"hello\"')")
    dot = ast_to_dot(ast)

    assert 'label="String: Ada said \\"hello\\""' in dot
