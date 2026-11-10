# Mini SQL Query Parser

An educational Compiler Construction mini project that performs lexical and
syntax analysis for a small SQL subset. It creates an Abstract Syntax Tree
(AST), displays it as text and Graphviz DOT, and reports friendly errors with
line and column positions.

> **This tool analyzes SQL syntax only. It does not execute queries or connect
> to a database.**

## Setup

Use Python 3.10 or newer.

```bash
cd mini-sql-query-parser
pip install -r requirements.txt
streamlit run app.py
```

Run the automated tests:

```bash
pytest
```

Use the command-line interface:

```bash
python main.py "SELECT name FROM students WHERE age >= 18;"
```

The CLI prints the tokens, validation result, and an indented AST. On Windows,
it configures UTF-8 output so the tree branch characters display correctly.

## Features

- Hand-written tokenizer with case-insensitive SQL keywords and 1-based source
  locations.
- Hand-written recursive-descent analyzer with one method per grammar rule.
- SELECT, INSERT, UPDATE, and DELETE statements, including multiple statements
  in one input.
- Expressions with arithmetic, comparison, `NOT`, `AND`, `OR`, parentheses,
  aggregates, `NULL`, and `IS [NOT] NULL`.
- AST output as an indented text tree and Graphviz DOT rendered by Streamlit.
- All lexical errors collected; first syntax error reported clearly.
- Sample valid and invalid queries in `examples/`.

## Project Layout

```text
mini-sql-query-parser/
├── app.py                 Streamlit UI
├── main.py                CLI entry point
├── lexer/                 Token definitions and tokenizer
├── sql_parser/            Recursive-descent analyzer and AST nodes
├── visualizer/            Text and Graphviz AST rendering
├── utils/                 Error classes and shared analysis entry point
├── tests/                 pytest coverage
├── examples/              Valid and invalid SQL examples
└── docs/                  Grammar and viva notes
```

## How It Works

1. The tokenizer reads characters and creates tokens such as `SELECT`,
   `IDENTIFIER`, `NUMBER`, and `GTE`.
2. If lexical errors exist, they are returned to the UI or CLI and parsing is
   skipped.
3. The recursive-descent analyzer checks the token order against the LL(1)
   grammar and creates an AST.
4. The visualizer recursively walks AST node labels and children to show the
   structure as text and Graphviz DOT.

See `docs/grammar.md`, `docs/first_follow.md`, `docs/token_table.md`, and
`docs/design_notes.md` for viva-ready explanations.

## Limitations

- This is a deliberately small SQL subset, not a full SQL implementation.
- It performs no execution and never connects to a database.
- Joins, subqueries, aliases, and SQL dialect-specific features are unsupported.
- It does no type checking, so syntactically valid expressions such as
  `WHERE 1 + 2` are accepted.
- It reports only the first syntax error, although it reports all lexical errors.
- It is not compatible with every SQL dialect.
