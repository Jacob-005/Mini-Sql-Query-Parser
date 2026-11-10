# Design Notes

## Architecture

The project has four small layers:

1. **Tokenizer** (`lexer/tokenizer.py`) reads raw SQL text and produces tokens
   with 1-based line and column positions.
2. **Recursive-descent analyzer** (`sql_parser/sql_parser.py`) reads those
   tokens and applies one Python method for each grammar rule.
3. **AST nodes** (`sql_parser/ast_nodes.py`) record only the meaningful SQL
   structure, not commas, parentheses, or other concrete punctuation.
4. **Visualizers** (`visualizer/tree_visualizer.py`) walk each node's `label`
   and `children` to create either an indented text AST or Graphviz DOT text.

`utils/analysis.py` connects the first two stages. It never runs the analyzer
if tokenization produced lexical errors. This guarantees an invalid input never
gets an AST. The Streamlit UI and CLI both call this shared function instead of
duplicating analysis logic.

## Data Flow

```text
SQL source
    |
    v
Tokenizer --> tokens + zero or more lexical errors
    |                         |
    | no lexical errors        v
    v                      show errors
SQLParser
    |
    +--> syntax error -------> show error
    |
    v
Program AST --> text tree and Graphviz DOT --> CLI / Streamlit UI
```

## Walkthrough: `SELECT * FROM t WHERE a = 1 OR b = 2 AND c = 3`

1. The tokenizer produces `SELECT`, `STAR`, `FROM`, `IDENTIFIER(t)`, `WHERE`,
   identifiers, numbers, comparison operators, `OR`, `AND`, and `EOF`.
2. `select_stmt()` recognizes `SELECT * FROM t`, then calls `where_clause()`.
3. The where clause calls `expression()`, which starts at `or_expr()`.
4. `or_expr()` calls `and_expr()` first. Therefore `b = 2 AND c = 3` becomes
   one `BinaryOp(AND)` before it is attached to `OR`.
5. The final AST has `BinaryOp(OR)` at the root. Its right child is
   `BinaryOp(AND)`, visibly demonstrating correct precedence.

## Error Strategy

Lexical analysis collects every lexical error so users can correct several
character-level mistakes in one pass. Syntax analysis stops at the first error,
which keeps messages focused and avoids building a misleading partial AST.
Every project error has a category, message, line, and column. The application
does not show raw Python exceptions to users.
