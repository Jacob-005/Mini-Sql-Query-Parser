"""Small, typed AST node classes for the Mini SQL grammar."""

from dataclasses import dataclass, field


class ASTNode:
    """Base class shared by every node in the abstract syntax tree (AST)."""

    @property
    def label(self) -> str:
        """Short text displayed by the AST visualizer."""
        return self.__class__.__name__

    @property
    def children(self) -> list["ASTNode"]:
        """Meaningful AST children, excluding punctuation tokens."""
        return []


@dataclass
class Program(ASTNode):
    statements: list[ASTNode]

    @property
    def children(self) -> list[ASTNode]:
        return self.statements


@dataclass
class TableName(ASTNode):
    name: str

    @property
    def label(self) -> str:
        return f"Table: {self.name}"


@dataclass
class ColumnRef(ASTNode):
    name: str
    table: str | None = None

    @property
    def label(self) -> str:
        qualified_name = f"{self.table}.{self.name}" if self.table else self.name
        return f"Column: {qualified_name}"


@dataclass
class Literal(ASTNode):
    value: str
    kind: str

    @property
    def label(self) -> str:
        return f"{self.kind.title()}: {self.value}"


@dataclass
class BinaryOp(ASTNode):
    operator: str
    left: ASTNode
    right: ASTNode

    @property
    def label(self) -> str:
        return f"Binary: {self.operator}"

    @property
    def children(self) -> list[ASTNode]:
        return [self.left, self.right]


@dataclass
class UnaryOp(ASTNode):
    operator: str
    operand: ASTNode

    @property
    def label(self) -> str:
        return f"Unary: {self.operator}"

    @property
    def children(self) -> list[ASTNode]:
        return [self.operand]


@dataclass
class IsNull(ASTNode):
    expression: ASTNode
    is_not: bool

    @property
    def label(self) -> str:
        return "IS NOT NULL" if self.is_not else "IS NULL"

    @property
    def children(self) -> list[ASTNode]:
        return [self.expression]


@dataclass
class Aggregate(ASTNode):
    function: str
    argument: ASTNode | None

    @property
    def label(self) -> str:
        return f"Aggregate: {self.function}"

    @property
    def children(self) -> list[ASTNode]:
        return [self.argument] if self.argument is not None else []


@dataclass
class WhereClause(ASTNode):
    condition: ASTNode

    @property
    def children(self) -> list[ASTNode]:
        return [self.condition]


@dataclass
class GroupClause(ASTNode):
    columns: list[ColumnRef]

    @property
    def children(self) -> list[ASTNode]:
        return self.columns


@dataclass
class OrderItem(ASTNode):
    column: ColumnRef
    direction: str | None

    @property
    def label(self) -> str:
        return f"Order item: {self.direction or 'DEFAULT'}"

    @property
    def children(self) -> list[ASTNode]:
        return [self.column]


@dataclass
class OrderClause(ASTNode):
    items: list[OrderItem]

    @property
    def children(self) -> list[ASTNode]:
        return self.items


@dataclass
class Assignment(ASTNode):
    column: ColumnRef
    value: ASTNode

    @property
    def children(self) -> list[ASTNode]:
        return [self.column, self.value]


@dataclass
class Row(ASTNode):
    values: list[Literal]

    @property
    def children(self) -> list[ASTNode]:
        return self.values


@dataclass
class SelectStatement(ASTNode):
    select_items: list[ASTNode] | None
    table: TableName
    where: WhereClause | None = None
    group_by: GroupClause | None = None
    order_by: OrderClause | None = None

    @property
    def label(self) -> str:
        return "SELECT *" if self.select_items is None else "SELECT"

    @property
    def children(self) -> list[ASTNode]:
        nodes = ([] if self.select_items is None else self.select_items.copy())
        nodes.append(self.table)
        nodes.extend(node for node in (self.where, self.group_by, self.order_by) if node)
        return nodes


@dataclass
class InsertStatement(ASTNode):
    table: TableName
    columns: list[ColumnRef] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)

    @property
    def children(self) -> list[ASTNode]:
        return [self.table, *self.columns, *self.rows]


@dataclass
class UpdateStatement(ASTNode):
    table: TableName
    assignments: list[Assignment]
    where: WhereClause | None = None

    @property
    def children(self) -> list[ASTNode]:
        nodes: list[ASTNode] = [self.table, *self.assignments]
        if self.where:
            nodes.append(self.where)
        return nodes


@dataclass
class DeleteStatement(ASTNode):
    table: TableName
    where: WhereClause | None = None

    @property
    def children(self) -> list[ASTNode]:
        return [self.table, *([self.where] if self.where else [])]
