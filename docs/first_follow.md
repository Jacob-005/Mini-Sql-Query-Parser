# FIRST and FOLLOW Sets

These sets cover the main non-terminals used by the recursive-descent analyzer.
`EOF` is included where a complete program may end. The token sets are shown
using token type names.

| Non-terminal | FIRST | FOLLOW |
| --- | --- | --- |
| `program` | `SELECT, INSERT, UPDATE, DELETE` | `EOF` |
| `statement` | `SELECT, INSERT, UPDATE, DELETE` | `SEMICOLON, EOF` |
| `select_stmt` | `SELECT` | `SEMICOLON, EOF` |
| `insert_stmt` | `INSERT` | `SEMICOLON, EOF` |
| `update_stmt` | `UPDATE` | `SEMICOLON, EOF` |
| `delete_stmt` | `DELETE` | `SEMICOLON, EOF` |
| `expression` | `NOT, MINUS, NUMBER, STRING, NULL, IDENTIFIER, COUNT, SUM, AVG, MIN, MAX, LPAREN` | `COMMA, RPAREN, SEMICOLON, EOF, FROM, WHERE, GROUP, ORDER` |
| `or_expr` | same as `expression` | same as `expression` |
| `and_expr` | same as `expression` | `OR` plus FOLLOW(`or_expr`) |
| `comparison` | same as `expression` | `AND, OR` plus FOLLOW(`and_expr`) |
| `primary` | `NUMBER, STRING, NULL, IDENTIFIER, COUNT, SUM, AVG, MIN, MAX, LPAREN` | arithmetic, comparison, logical operators and FOLLOW(`expression`) |
| `column_ref` | `IDENTIFIER` | `COMMA, RPAREN, ASC, DESC, EQ, NEQ, LT, GT, LTE, GTE, IS` and clause boundaries |
| `where_clause` | `WHERE` | `GROUP, ORDER, SEMICOLON, EOF` |
| `group_clause` | `GROUP` | `ORDER, SEMICOLON, EOF` |
| `order_clause` | `ORDER` | `SEMICOLON, EOF` |

## Why the grammar is LL(1)

At each choice, one look-ahead token selects a unique alternative. For example,
`statement` starts with four distinct keywords, `primary` has distinct starts
for literals, identifiers, aggregates, and parentheses, and `select_list`
distinguishes `STAR` from an expression. Optional clauses begin with their own
keywords (`WHERE`, `GROUP`, and `ORDER`). Repetition is expressed with loops,
not left-recursive rules, so one token of look-ahead is enough throughout this
subset.
