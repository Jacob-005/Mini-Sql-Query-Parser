"""Render any ASTNode as an indented text tree or Graphviz DOT graph."""

from sql_parser.ast_nodes import ASTNode


def ast_to_text(root: ASTNode) -> str:
    """Return a readable AST using standard tree branch characters."""
    lines = [root.label]
    _add_text_children(root, lines, "")
    return "\n".join(lines)


def _add_text_children(node: ASTNode, lines: list[str], prefix: str) -> None:
    """Append one node's children with indentation that preserves tree shape."""
    children = node.children
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{child.label}")
        child_prefix = prefix + ("    " if is_last else "│   ")
        _add_text_children(child, lines, child_prefix)


def ast_to_dot(root: ASTNode) -> str:
    """Return Graphviz DOT text for an AST without needing a Graphviz install."""
    lines = [
        "digraph AST {",
        "  rankdir=TB;",
        '  node [shape=box, style="rounded", fontname="Arial"];',
    ]
    next_node_id = 0

    def add_node(node: ASTNode) -> str:
        """Add a DOT node, then recursively add and connect its children."""
        nonlocal next_node_id
        node_id = f"node_{next_node_id}"
        next_node_id += 1
        lines.append(f'  {node_id} [label="{_escape_dot_label(node.label)}"];')

        for child in node.children:
            child_id = add_node(child)
            lines.append(f"  {node_id} -> {child_id};")
        return node_id

    add_node(root)
    lines.append("}")
    return "\n".join(lines)


def _escape_dot_label(label: str) -> str:
    """Escape text that would otherwise make a DOT string invalid."""
    return label.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
