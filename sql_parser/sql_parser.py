"""Hand-written recursive-descent analyzer for the Mini SQL grammar."""

from lexer.token_types import Token, TokenType
from sql_parser.ast_nodes import (
    ASTNode,
    Aggregate,
    Assignment,
    BinaryOp,
    ColumnRef,
    DeleteStatement,
    GroupClause,
    InsertStatement,
    IsNull,
    Literal,
    OrderClause,
    OrderItem,
    Program,
    Row,
    SelectStatement,
    TableName,
    UnaryOp,
    UpdateStatement,
    WhereClause,
)
from utils.error_handler import SQLSyntaxError


class SQLParser:
    """Build an AST from tokens using one method for each grammar rule."""

    COMPARISON_TYPES = {
        TokenType.EQ,
        TokenType.NEQ,
        TokenType.LT,
        TokenType.GT,
        TokenType.LTE,
        TokenType.GTE,
    }
    AGGREGATE_TYPES = {
        TokenType.COUNT,
        TokenType.SUM,
        TokenType.AVG,
        TokenType.MIN,
        TokenType.MAX,
    }
    RESERVED_KEYWORD_TYPES = {
        TokenType.SELECT,
        TokenType.FROM,
        TokenType.WHERE,
        TokenType.GROUP,
        TokenType.BY,
        TokenType.ORDER,
        TokenType.ASC,
        TokenType.DESC,
        TokenType.INSERT,
        TokenType.INTO,
        TokenType.VALUES,
        TokenType.UPDATE,
        TokenType.SET,
        TokenType.DELETE,
        TokenType.AND,
        TokenType.OR,
        TokenType.NOT,
        TokenType.NULL,
        TokenType.IS,
        TokenType.COUNT,
        TokenType.SUM,
        TokenType.AVG,
        TokenType.MIN,
        TokenType.MAX,
    }
    EXPECTED_DISPLAY = {
        "RPAREN": "')'",
        "LPAREN": "'('",
        "EQ": "'='",
        "SEMICOLON": "';'",
        "IDENTIFIER": "identifier",
    }

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def analyze(self) -> Program:
        """Analyze a complete token list and return its AST program node."""
        return self.program()

    def program(self) -> Program:
        """program -> statement (SEMICOLON statement)* SEMICOLON? EOF"""
        statements = [self.statement()]

        while self._match(TokenType.SEMICOLON):
            if self._check(TokenType.EOF):
                break
            statements.append(self.statement())

        self._consume(TokenType.EOF, "SEMICOLON or end of input")
        return Program(statements)

    def statement(self) -> ASTNode:
        """statement -> select_stmt | insert_stmt | update_stmt | delete_stmt"""
        if self._check(TokenType.SELECT):
            return self.select_stmt()
        if self._check(TokenType.INSERT):
            return self.insert_stmt()
        if self._check(TokenType.UPDATE):
            return self.update_stmt()
        if self._check(TokenType.DELETE):
            return self.delete_stmt()
        self._raise_expected("SELECT, INSERT, UPDATE, or DELETE")

    def select_stmt(self) -> SelectStatement:
        """Parse a SELECT statement and its optional clauses."""
        self._consume(TokenType.SELECT, "SELECT")
        select_items = self.select_list()
        self._consume(TokenType.FROM, "FROM")
        table = self.table_name()
        where = self.where_clause() if self._check(TokenType.WHERE) else None
        group_by = self.group_clause() if self._check(TokenType.GROUP) else None
        order_by = self.order_clause() if self._check(TokenType.ORDER) else None
        return SelectStatement(select_items, table, where, group_by, order_by)

    def select_list(self) -> list[ASTNode] | None:
        """select_list -> STAR | select_item (COMMA select_item)*"""
        if self._match(TokenType.STAR):
            return None

        items = [self.select_item()]
        while self._match(TokenType.COMMA):
            items.append(self.select_item())
        return items

    def select_item(self) -> ASTNode:
        """select_item -> expression"""
        return self.expression()

    def insert_stmt(self) -> InsertStatement:
        """Parse INSERT INTO with optional column names and one or more rows."""
        self._consume(TokenType.INSERT, "INSERT")
        self._consume(TokenType.INTO, "INTO")
        table = self.table_name()
        columns = self.column_list() if self._check(TokenType.LPAREN) else []
        self._consume(TokenType.VALUES, "VALUES")
        rows = [self.row()]
        while self._match(TokenType.COMMA):
            rows.append(self.row())
        return InsertStatement(table, columns, rows)

    def column_list(self) -> list[ColumnRef]:
        """column_list -> LPAREN column_name (COMMA column_name)* RPAREN"""
        self._consume(TokenType.LPAREN, "LPAREN")
        columns = [self.column_name()]
        while self._match(TokenType.COMMA):
            columns.append(self.column_name())
        self._consume(TokenType.RPAREN, "RPAREN")
        return columns

    def row(self) -> Row:
        """row -> LPAREN literal (COMMA literal)* RPAREN"""
        self._consume(TokenType.LPAREN, "LPAREN")
        values = [self.literal()]
        while self._match(TokenType.COMMA):
            values.append(self.literal())
        self._consume(TokenType.RPAREN, "RPAREN")
        return Row(values)

    def literal(self) -> Literal:
        """literal -> MINUS? NUMBER | STRING | NULL"""
        is_negative = self._match(TokenType.MINUS)
        if self._match(TokenType.NUMBER):
            value = self._previous().lexeme
            return Literal(f"-{value}" if is_negative else value, "number")
        if is_negative:
            self._raise_expected("NUMBER")
        if self._match(TokenType.STRING):
            return Literal(self._string_value(self._previous().lexeme), "string")
        if self._match(TokenType.NULL):
            return Literal("NULL", "null")
        self._raise_expected("literal")

    def update_stmt(self) -> UpdateStatement:
        """Parse UPDATE assignments followed by an optional WHERE clause."""
        self._consume(TokenType.UPDATE, "UPDATE")
        table = self.table_name()
        self._consume(TokenType.SET, "SET")
        assignments = [self.assignment()]
        while self._match(TokenType.COMMA):
            assignments.append(self.assignment())
        where = self.where_clause() if self._check(TokenType.WHERE) else None
        return UpdateStatement(table, assignments, where)

    def assignment(self) -> Assignment:
        """assignment -> column_name EQ expression"""
        column = self.column_name()
        self._consume(TokenType.EQ, "EQ")
        return Assignment(column, self.expression())

    def delete_stmt(self) -> DeleteStatement:
        """Parse DELETE FROM with an optional WHERE clause."""
        self._consume(TokenType.DELETE, "DELETE")
        self._consume(TokenType.FROM, "FROM")
        table = self.table_name()
        where = self.where_clause() if self._check(TokenType.WHERE) else None
        return DeleteStatement(table, where)

    def where_clause(self) -> WhereClause:
        """where_clause -> WHERE expression"""
        self._consume(TokenType.WHERE, "WHERE")
        return WhereClause(self.expression())

    def group_clause(self) -> GroupClause:
        """group_clause -> GROUP BY column_ref (COMMA column_ref)*"""
        self._consume(TokenType.GROUP, "GROUP")
        self._consume(TokenType.BY, "BY")
        columns = [self.column_ref()]
        while self._match(TokenType.COMMA):
            columns.append(self.column_ref())
        return GroupClause(columns)

    def order_clause(self) -> OrderClause:
        """order_clause -> ORDER BY order_item (COMMA order_item)*"""
        self._consume(TokenType.ORDER, "ORDER")
        self._consume(TokenType.BY, "BY")
        items = [self.order_item()]
        while self._match(TokenType.COMMA):
            items.append(self.order_item())
        return OrderClause(items)

    def order_item(self) -> OrderItem:
        """order_item -> column_ref (ASC | DESC)?"""
        column = self.column_ref()
        direction = None
        if self._match(TokenType.ASC, TokenType.DESC):
            direction = self._previous().lexeme.upper()
        return OrderItem(column, direction)

    def expression(self) -> ASTNode:
        """expression -> or_expr"""
        return self.or_expr()

    def or_expr(self) -> ASTNode:
        """or_expr -> and_expr (OR and_expr)*"""
        node = self.and_expr()
        while self._match(TokenType.OR):
            node = BinaryOp(self._previous().lexeme.upper(), node, self.and_expr())
        return node

    def and_expr(self) -> ASTNode:
        """and_expr -> not_expr (AND not_expr)*"""
        node = self.not_expr()
        while self._match(TokenType.AND):
            node = BinaryOp(self._previous().lexeme.upper(), node, self.not_expr())
        return node

    def not_expr(self) -> ASTNode:
        """not_expr -> NOT not_expr | comparison"""
        if self._match(TokenType.NOT):
            return UnaryOp(self._previous().lexeme.upper(), self.not_expr())
        return self.comparison()

    def comparison(self) -> ASTNode:
        """Parse a single comparison or an IS [NOT] NULL condition."""
        node = self.additive()
        if self._match(*self.COMPARISON_TYPES):
            return BinaryOp(self._previous().lexeme, node, self.additive())
        if self._match(TokenType.IS):
            is_not = self._match(TokenType.NOT)
            self._consume(TokenType.NULL, "NULL")
            return IsNull(node, is_not)
        return node

    def additive(self) -> ASTNode:
        """additive -> term ((PLUS | MINUS) term)*"""
        node = self.term()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            node = BinaryOp(self._previous().lexeme, node, self.term())
        return node

    def term(self) -> ASTNode:
        """term -> unary ((STAR | SLASH) unary)*"""
        node = self.unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            node = BinaryOp(self._previous().lexeme, node, self.unary())
        return node

    def unary(self) -> ASTNode:
        """unary -> MINUS unary | primary"""
        if self._match(TokenType.MINUS):
            return UnaryOp(self._previous().lexeme, self.unary())
        return self.primary()

    def primary(self) -> ASTNode:
        """Parse number, string, NULL, a column, aggregate, or parentheses."""
        if self._match(TokenType.NUMBER):
            return Literal(self._previous().lexeme, "number")
        if self._match(TokenType.STRING):
            return Literal(self._string_value(self._previous().lexeme), "string")
        if self._match(TokenType.NULL):
            return Literal("NULL", "null")
        if self._check(*self.AGGREGATE_TYPES):
            return self.aggregate()
        if self._check(TokenType.IDENTIFIER):
            return self.column_ref()
        if self._match(TokenType.LPAREN):
            node = self.expression()
            self._consume(TokenType.RPAREN, "RPAREN")
            return node
        self._raise_expected("expression")

    def aggregate(self) -> Aggregate:
        """aggregate -> (COUNT|SUM|AVG|MIN|MAX) LPAREN (STAR | expression) RPAREN"""
        function = self._advance().lexeme.upper()
        self._consume(TokenType.LPAREN, "LPAREN")
        argument = None if self._match(TokenType.STAR) else self.expression()
        self._consume(TokenType.RPAREN, "RPAREN")
        return Aggregate(function, argument)

    def column_ref(self) -> ColumnRef:
        """column_ref -> IDENTIFIER (DOT IDENTIFIER)?"""
        first_name = self._consume(TokenType.IDENTIFIER, "IDENTIFIER").lexeme
        if self._match(TokenType.DOT):
            second_name = self._consume(TokenType.IDENTIFIER, "IDENTIFIER").lexeme
            return ColumnRef(second_name, first_name)
        return ColumnRef(first_name)

    def table_name(self) -> TableName:
        """table_name -> IDENTIFIER"""
        return TableName(self._consume(TokenType.IDENTIFIER, "IDENTIFIER").lexeme)

    def column_name(self) -> ColumnRef:
        """column_name -> IDENTIFIER"""
        return ColumnRef(self._consume(TokenType.IDENTIFIER, "IDENTIFIER").lexeme)

    def _match(self, *types: TokenType) -> bool:
        """Consume the current token when it has one of the requested types."""
        if self._check(*types):
            self._advance()
            return True
        return False

    def _consume(self, token_type: TokenType, expected: str) -> Token:
        """Consume one expected token or raise a location-aware syntax error."""
        if self._check(token_type):
            return self._advance()
        self._raise_expected(expected)

    def _check(self, *types: TokenType) -> bool:
        """Check the current token without consuming it."""
        return self._peek().type in types

    def _advance(self) -> Token:
        """Consume and return the current token."""
        token = self._peek()
        if not self._is_at_end():
            self.current += 1
        return token

    def _previous(self) -> Token:
        """Return the token most recently consumed."""
        return self.tokens[self.current - 1]

    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.current]

    def _is_at_end(self) -> bool:
        return self._peek().type is TokenType.EOF

    def _raise_expected(self, expected: str) -> None:
        """Raise the project's standard expected-versus-found syntax message."""
        token = self._peek()
        expected_display = self._format_expected(expected)

        if (
            expected_display == "identifier"
            and token.type is not TokenType.IDENTIFIER
            and token.type in self.RESERVED_KEYWORD_TYPES
        ):
            raise SQLSyntaxError(
                f"Expected identifier but found reserved keyword '{token.lexeme.lower()}'",
                token.line,
                token.column,
            )

        found = "end of input" if token.type is TokenType.EOF else f"'{token.lexeme}'"
        raise SQLSyntaxError(
            f"Expected {expected_display} but found {found}", token.line, token.column
        )

    @classmethod
    def _format_expected(cls, expected: str) -> str:
        """Convert internal token names to user-facing symbols where appropriate."""
        formatted = expected
        for token_name, replacement in cls.EXPECTED_DISPLAY.items():
            formatted = formatted.replace(token_name, replacement)
        return formatted

    @staticmethod
    def _string_value(lexeme: str) -> str:
        """Remove SQL quotes and convert doubled quotes to one quote for the AST."""
        return lexeme[1:-1].replace("''", "'")
