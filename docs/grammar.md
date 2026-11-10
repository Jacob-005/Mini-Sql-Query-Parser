# Mini SQL Grammar

The Mini SQL Query Parser accepts this deliberately small SQL subset. Terminals
are written in uppercase and optional or repeated parts use EBNF notation.

```ebnf
program       = statement, { SEMICOLON, statement }, [ SEMICOLON ], EOF ;
statement     = select_stmt | insert_stmt | update_stmt | delete_stmt ;

select_stmt   = SELECT, select_list, FROM, table_name,
                [ where_clause ], [ group_clause ], [ order_clause ] ;
select_list   = STAR | select_item, { COMMA, select_item } ;
select_item   = expression ;
insert_stmt   = INSERT, INTO, table_name, [ column_list ], VALUES, row,
                { COMMA, row } ;
column_list   = LPAREN, column_name, { COMMA, column_name }, RPAREN ;
row           = LPAREN, literal, { COMMA, literal }, RPAREN ;
literal       = [ MINUS ], NUMBER | STRING | NULL ;
update_stmt   = UPDATE, table_name, SET, assignment, { COMMA, assignment },
                [ where_clause ] ;
assignment    = column_name, EQ, expression ;
delete_stmt   = DELETE, FROM, table_name, [ where_clause ] ;

where_clause  = WHERE, expression ;
group_clause  = GROUP, BY, column_ref, { COMMA, column_ref } ;
order_clause  = ORDER, BY, order_item, { COMMA, order_item } ;
order_item    = column_ref, [ ASC | DESC ] ;

expression    = or_expr ;
or_expr       = and_expr, { OR, and_expr } ;
and_expr      = not_expr, { AND, not_expr } ;
not_expr      = NOT, not_expr | comparison ;
comparison    = additive, [ ((EQ | NEQ | LT | GT | LTE | GTE), additive)
                | (IS, [ NOT ], NULL) ] ;
additive      = term, { (PLUS | MINUS), term } ;
term          = unary, { (STAR | SLASH), unary } ;
unary         = MINUS, unary | primary ;
primary       = NUMBER | STRING | NULL | column_ref | aggregate
                | LPAREN, expression, RPAREN ;
aggregate     = (COUNT | SUM | AVG | MIN | MAX), LPAREN,
                (STAR | expression), RPAREN ;
column_ref    = IDENTIFIER, [ DOT, IDENTIFIER ] ;
table_name    = IDENTIFIER ;
column_name   = IDENTIFIER ;
```

## Precedence and left associativity

The expression rules are arranged from lowest precedence (`OR`) to highest
precedence (primary values). A lower rule calls the next higher rule, so an
`AND` expression is completed before an enclosing `OR` expression. Repeated
operator parts use loops in the recursive-descent analyzer. Each loop builds a
new node from the previous left-hand node, which makes `a - b - c` parse as
`(a - b) - c`.

There is no left recursion. For example, instead of `additive -> additive +
term`, the grammar uses `additive -> term { (+|-) term }`. This lets one method
choose its alternative from the next token without calling itself forever.
