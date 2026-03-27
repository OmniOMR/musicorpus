from .CocoBbox import CocoBbox
from mung.graph import NotationGraph, Node
from copy import deepcopy


def crop_mung(mung_graph: NotationGraph, bbox: CocoBbox):
    """
    Returns a cropped view at the given MuNG document.
    Returned nodes are clones of the original. IDs are preserved.
    Nodes outside of the cropped region are removed.
    Node positions are updated to be positioned relative to the cropped bbox.
    """
    # do a clone first
    mung_graph = deepcopy(mung_graph)

    # remove nodes outside the bbox
    for node in list(mung_graph.vertices):
        t, l = node.middle
        if t < bbox.top or t > bbox.bottom or l < bbox.left or l > bbox.right:
            remove_precedence_edges_for_node(mung_graph, node)
            mung_graph.remove_vertex(node.id)
    
    # translate nodes into the crop coordinate system
    for node in mung_graph.vertices:
        node.translate(
            down=-bbox.top,
            right=-bbox.left,
        )
    
    # return the new graph
    return mung_graph


def remove_precedence_edges_for_node(mung_graph: NotationGraph, node: Node):
    in_edges: list[tuple[int, int]] = [
        (id, node.id) for id in node.data.get("precedence_inlinks", [])
    ]
    out_edges: list[tuple[int, int]] = [
        (node.id, id) for id in node.data.get("precedence_outlinks", [])
    ]
    for source, target in in_edges + out_edges:
        mung_graph[source].data["precedence_outlinks"].remove(target)
        mung_graph[target].data["precedence_inlinks"].remove(source)
