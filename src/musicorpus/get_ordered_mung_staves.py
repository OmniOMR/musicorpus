from mung.graph import NotationGraph
from mung.node import Node


def staff_sort_key(node: Node) -> float:
    """Orders staves top-down, breaking ties slightly left-to-right."""
    return node.top + node.left * 0.1


def get_ordered_mung_staves(mung_graph: NotationGraph) -> list[Node]:
    """Returns staves in the mung document, ordered top-down
    in the same way in which they are numbered in subdivisions."""
    # get all mung staves, sorted top-down (and slightly left-to-right)
    mung_staves = [
        node for node in mung_graph.vertices
        if node.class_name == "staff"
    ]
    mung_staves.sort(key=staff_sort_key)
    return mung_staves
