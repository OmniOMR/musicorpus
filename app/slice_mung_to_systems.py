from mung.graph import NotationGraph, group_staffs_into_systems
from mung.node import Node
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class MungSystem:
    number: int
    """System number within the page, 1-based"""
    
    staves: list[Node]
    """Mung nodes of class "staff" that belong to this system, sorted top-down."""

    crop_bbox_trbl: tuple[int, int, int, int]
    """Crop-box for the image in pixels (top, right, bottom, left),
    guaranteed to not overflow the image"""

    nodes: list[Node]
    """All MuNG nodes that belong into the system crop, forming a valid graph"""


def slice_mung_to_systems(
        mung_graph: NotationGraph,
        image_width: int,
        image_height: int,
):
    """Slices one page of MuNG into systems and provides additional metadata
    for each of those systems. Systems are sorted top-down."""
    grouped_staves = group_staffs_into_systems(mung_graph.vertices)
    grouped_staves = list(filter(lambda g: len(g) != 0, grouped_staves))
    grouped_staves.sort(key=lambda g: g[0].top) # sort top-down

    assert len(set(len(group) for group in grouped_staves)), \
        "Detected systems do not have equal number of staves"

    mung_systems: list[MungSystem] = []

    for i, group in enumerate(grouped_staves):
        # compute tight cropbox
        top = min(staff.top for staff in group)
        right = max(staff.right for staff in group)
        bottom = max(staff.bottom for staff in group)
        left = min(staff.left for staff in group)

        # get avg staff height (from bbox or mask)
        # staff_height = sum(staff.height for staff in group) // len(group)
        staff_height = int(sum(
            staff.mask.sum(axis=0).mean()
            for staff in group
        ) / len(group))

        # enlarge cropbox by staff height
        top -= staff_height
        right += staff_height
        bottom += staff_height
        left -= staff_height

        # clamp cropbox to page
        if top < 0: top = 0
        if right > image_width: right = image_width
        if bottom > image_height: bottom = image_height
        if left < 0: left = 0

        # get mung sub-graph in the bbox
        system_graph = deepcopy(mung_graph)
        for node in list(system_graph.vertices): # iterate clone to delete from original
            t, l = node.middle
            if t < top or t > bottom or l < left or l > right:
                system_graph.remove_from_precedence(node.id)
                system_graph.remove_vertex(node.id)
        
        # translate nodes into the crop coordinate system
        for node in system_graph.vertices:
            node.translate(
                down=-top,
                right=-left,
            )

        # build out the description object
        mung_systems.append(MungSystem(
            number=i+1,
            staves=list(sorted(group, key=lambda s: s.top)),
            crop_bbox_trbl=(top, right, bottom, left),
            nodes=system_graph.vertices,
        ))

    return mung_systems
