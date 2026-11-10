# Token Table

The tokenizer scans source from left to right. Regex is used only to recognize
one identifier or number token at the current position; no regex is used to
parse SQL grammar.

| Token type | Pattern or spelling | Example | Notes |
| --- | --- | --- | --- |
| `SELECT`, `FROM`, `WHERE`, `GROUP`, `BY`, `ORDER`, `ASC`, `DESC` | Case-insensitive keyword | `select`, `FrOm` | The original spelling is kept in the token. |
| `INSERT`, `INTO`, `VALUES`, `UPDATE`, `SET`, `DELETE` | Case-insensitive keyword | `insert` | One distinct token type exists for each keyword. |
| `AND`, `OR`, `NOT`, `NULL`, `IS` | Case-insensitive keyword | `IS NOT NULL` | Used in expressions and comparisons. |
| `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` | Case-insensitive keyword | `COUNT(*)` | Used only by the aggregate grammar rule. |
| `IDENTIFIER` | `[A-Za-z_][A-Za-z0-9_]*` | `student_2` | A word not found in the keyword table. |
| `NUMBER` | `\d+(\.\d+)?` | `42`, `12.50` | A leading `-` is a separate `MINUS` token. |
| `STRING` | Single-quoted, scanned manually | `'Ada Lovelace'` | `''` inside a string means one quote. |
| `PLUS`, `MINUS`, `STAR`, `SLASH` | `+`, `-`, `*`, `/` | `score + 1` | Arithmetic operators. |
| `EQ`, `NEQ`, `LT`, `GT`, `LTE`, `GTE` | `=`, `!=`/`<>`, `<`, `>`, `<=`, `>=` | `age >= 18` | Two-character operators are checked first. |
| `COMMA`, `DOT`, `LPAREN`, `RPAREN`, `SEMICOLON` | `,`, `.`, `(`, `)`, `;` | `table.column` | Punctuation used by grammar rules. |
| `EOF` | End of source | — | Added after every input, even when lexical errors exist. |

## Ignored text and malformed input

Whitespace and `--` line comments are skipped while line and column counters
continue to move. Invalid characters, unterminated strings, and malformed
numbers such as `1.2.3` and `12abc` are reported as lexical errors. The scanner
continues after an error so the user can see all lexical mistakes at once.
