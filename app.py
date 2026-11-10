"""Streamlit interface for the Mini SQL Query Parser."""

import streamlit as st

from utils.analysis import AnalysisResult, analyze_sql
from visualizer.tree_visualizer import ast_to_dot, ast_to_text


SAMPLE_QUERIES = {
    "Valid SELECT with clauses": (
        "SELECT department, COUNT(*) FROM employees "
        "WHERE salary >= 50000 GROUP BY department ORDER BY department ASC;"
    ),
    "Valid INSERT with rows": (
        "INSERT INTO students (id, name, score) VALUES "
        "(1, 'Ada Lovelace', 91.5), (2, 'Lin', 88);"
    ),
    "Valid UPDATE": "UPDATE students SET score = score + 5 WHERE name IS NOT NULL;",
    "Valid multiple statements": "SELECT * FROM students; DELETE FROM logs WHERE id = 4;",
    "Invalid missing FROM": "SELECT name students;",
    "Invalid incomplete condition": "SELECT name FROM students WHERE age >= ;",
    "Invalid lexical character": "SELECT @ FROM students;",
}


def token_rows(result: AnalysisResult) -> list[dict[str, str | int]]:
    """Convert tokens to simple rows Streamlit can display as a table."""
    return [
        {
            "Type": token.type.name,
            "Value": token.lexeme if token.lexeme else "<EOF>",
            "Line": token.line,
            "Column": token.column,
        }
        for token in result.tokens
    ]


def display_errors(result: AnalysisResult) -> None:
    """Show friendly lexical or syntax diagnostics from one analysis result."""
    for error in result.lexical_errors:
        st.error(
            f"{error.category}: {error.message} "
            f"(line {error.line}, column {error.column})"
        )
    if result.syntax_error:
        error = result.syntax_error
        st.error(
            f"{error.category}: {error.message} "
            f"(line {error.line}, column {error.column})"
        )


def display_valid_ast(result: AnalysisResult) -> None:
    """Display text and Graphviz versions of each successfully analyzed AST."""
    if result.ast is None:
        st.error("Unexpected internal error")
        return
    for number, statement in enumerate(result.ast.statements, start=1):
        st.subheader(f"Statement {number} AST")
        text_column, graph_column = st.columns(2)
        with text_column:
            st.caption("Indented text AST")
            st.code(ast_to_text(statement), language=None)
        with graph_column:
            st.caption("Graphviz AST")
            st.graphviz_chart(ast_to_dot(statement), use_container_width=True)


def main() -> None:
    """Create the Streamlit page and handle user analysis requests."""
    st.set_page_config(page_title="Mini SQL Query Parser", page_icon="🧩", layout="wide")
    st.title("Mini SQL Query Parser")
    st.info(
        "This tool analyzes SQL syntax only. It does not execute queries or "
        "connect to a database."
    )

    if "sql_text" not in st.session_state:
        st.session_state.sql_text = "SELECT name, age FROM students WHERE age >= 18;"

    with st.sidebar:
        st.header("Sample Queries")
        selected_sample = st.selectbox("Choose a sample", ["Choose a sample", *SAMPLE_QUERIES])
        if st.button("Load selected sample", disabled=selected_sample == "Choose a sample"):
            st.session_state.sql_text = SAMPLE_QUERIES[selected_sample]
            st.session_state.pop("analysis_result", None)
            st.rerun()

    st.text_area("SQL input", key="sql_text", height=180)
    if st.button("Analyze", type="primary"):
        try:
            st.session_state.analysis_result = analyze_sql(st.session_state.sql_text)
        except Exception:
            st.session_state.analysis_result = None
            st.error("Unexpected internal error")
            return

    result = st.session_state.get("analysis_result")
    if result is None:
        return

    st.subheader("Tokens")
    st.dataframe(token_rows(result), hide_index=True, use_container_width=True)

    if result.is_valid:
        st.success("Valid SQL syntax.")
        display_valid_ast(result)
    else:
        st.error("Invalid SQL syntax.")
        display_errors(result)


if __name__ == "__main__":
    main()
