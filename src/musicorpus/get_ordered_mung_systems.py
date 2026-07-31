from mung.graph import NotationGraph, group_staffs_into_systems
from mung.node import Node

from .get_ordered_mung_staves import staff_sort_key
from .hidden_prints import HiddenPrints


def get_ordered_mung_systems(mung_graph: NotationGraph) -> list[list[Node]]:
    """Returns systems (as lists of staves) in the mung document,
    ordered top-down in the same way in which they are
    numbered in subdivisions."""
    # get all mung staves, sorted top-down (and slightly left-to-right)
    with HiddenPrints():
        systems = group_staffs_into_systems(mung_graph.vertices)
    
    # discard empty systems
    systems = list(filter(lambda g: len(g) != 0, systems))
    
    # sort like staves
    systems.sort(key=lambda system: staff_sort_key(system[0]))
    
    return systems
