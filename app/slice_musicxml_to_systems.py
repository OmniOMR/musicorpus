import copy
import xml.etree.ElementTree as ET
from lmx.symbolic.split_part_to_systems \
    import split_part_to_systems, Page, System


def slice_musicxml_to_systems(
        musicxml_tree: ET.ElementTree
) -> list[ET.ElementTree]:
    """Slices one-page MusicXML into per-system MusicXML files"""
    
    # extract important elements from the input file
    root = musicxml_tree.getroot()
    assert root is not None
    assert root.tag == "score-partwise"

    identification_element = root.find("identification")
    assert identification_element is not None

    defaults_element = root.find("defaults")
    assert defaults_element is not None

    part_list_element = root.find("part-list")
    assert part_list_element is not None

    part_elements = root.findall("part")
    assert len(part_elements) > 0
    assert all("id" in p.attrib for p in part_elements)

    part_ids = [p.attrib["id"] for p in part_elements]

    # slice parts to systems
    systems_per_part: dict[str, list[System]] = {}
    for part_index, part_id in enumerate(part_ids):
        pages: list[Page] = split_part_to_systems(
            part=part_elements[part_index],
        )
        assert len(pages) == 1, "There should be no page breaks!"
        assert len(pages[0].systems) > 0, "At least one system is expeted"
        systems_per_part[part_id] = pages[0].systems
    
    # get system count
    system_counts = set(len(systems_per_part[part_id]) for part_id in part_ids)
    assert len(system_counts) == 1, \
        "There are differing number of systems between parts"
    system_count = system_counts.pop()
    
    # emit per-system trees
    trees: list[ET.ElementTree] = []
    for system_index in range(system_count):
        root = ET.Element("score-partwise", {"version": "3.1"})
        root.append(copy.deepcopy(identification_element))
        root.append(copy.deepcopy(defaults_element))
        root.append(copy.deepcopy(part_list_element))

        for part_index, part_id in enumerate(part_ids):
            root.append(systems_per_part[part_id][system_index].part)

        trees.append(ET.ElementTree(root))
    
    return trees
