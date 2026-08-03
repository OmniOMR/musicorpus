"""Splits a grandstaff MusicXML transcription into two staff-level ones."""

import copy
import xml.etree.ElementTree as ET

from lmx.musicxml.grandstaff.unzip_grandstaff import unzip_grandstaff

HEAD_ELEMENTS = (
    "work",
    "movement-number",
    "movement-title",
    "identification",
    "defaults",
    "credit",
)
"""Elements that may precede `part-list` in a `score-partwise` document.

Copied onto both outputs in this order, which is the order MusicXML requires.
OLiMPiC files carry none of them, but a document assembled by hand should not
depend on that.
"""


class NotASingleGrandstaff(Exception):
    """Raised when the input is not one part of two staves, which is all this
    handles. OLiMPiC samples always are; anything else is a broken sample."""


def unzip_grandstaff_musicxml(root: ET.Element) -> tuple[ET.ElementTree, ET.ElementTree]:
    """Returns the (upper, lower) staff transcriptions of a grandstaff document.

    Raises `ContainsTruePianoformMusicException` when the notation cannot be
    separated onto two staves without breaking it — a voice that crosses from
    one staff to the other, which is ordinary in piano music. The caller is
    expected to skip such a grandstaff rather than force the split: forcing it
    would silently produce a transcription that does not match its image.
    """
    if root.tag != "score-partwise":
        raise NotASingleGrandstaff(f"Expected a <score-partwise> document, got <{root.tag}>")

    parts = root.findall("part")
    if len(parts) != 1:
        raise NotASingleGrandstaff(f"Expected exactly one <part>, got {len(parts)}")
    part = parts[0]

    part_id = part.get("id")
    if part_id is None:
        raise NotASingleGrandstaff("The <part> element has no id")

    # this is what raises on music that cannot be separated
    upper_part, lower_part = unzip_grandstaff(
        part,
        upper_part_id=part_id,
        lower_part_id=part_id,
        force_split=False,
    )

    return (
        _build_score(source_root=root, part_id=part_id, part_element=upper_part),
        _build_score(source_root=root, part_id=part_id, part_element=lower_part),
    )


def _build_score(source_root: ET.Element, part_id: str, part_element: ET.Element) -> ET.ElementTree:
    """Wraps a single `<part>` back up into a whole MusicXML document.

    `lmx.unzip_grandstaff` hands back bare `<part>` elements, so the document
    around them — the header elements and the `<part-list>` entry naming this
    part — is carried over from the input.
    """
    root = ET.Element("score-partwise", {"version": source_root.get("version", "3.1")})

    for tag in HEAD_ELEMENTS:
        for element in source_root.findall(tag):
            root.append(copy.deepcopy(element))

    part_list = ET.Element("part-list")
    root.append(part_list)
    source_score_part = source_root.find(f"part-list/score-part[@id='{part_id}']")
    if source_score_part is not None:
        part_list.append(copy.deepcopy(source_score_part))
    else:
        # the document has to name its part, even when the input failed to
        score_part = ET.SubElement(part_list, "score-part", {"id": part_id})
        ET.SubElement(score_part, "part-name").text = part_id

    root.append(part_element)

    return ET.ElementTree(root)
