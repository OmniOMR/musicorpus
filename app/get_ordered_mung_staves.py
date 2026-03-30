from mung.node import Node
from mung.graph import NotationGraph


SORT_KEY = lambda node: node.top + node.left * 0.1


def get_ordered_mung_staves(mung_graph: NotationGraph) -> list[Node]:
    """Returns staves in the mung document, ordered top-down
    in the same way in which they are numbered in subdivisions."""
    # get all mung staves, sorted top-down (and slightly left-to-right)
    mung_staves = [
        node for node in mung_graph.vertices
        if node.class_name == "staff"
    ]
    mung_staves.sort(key=SORT_KEY)
    return mung_staves
