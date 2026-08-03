"""States in a MusicXML document that its system and page breaks are explicit."""

import xml.etree.ElementTree as ET

SUPPORTED_BREAK_ATTRIBUTES = ("new-system", "new-page")
"""The two `<print>` attributes whose explicitness has to be declared."""

ELEMENTS_AFTER_IDENTIFICATION = ("defaults", "credit", "part-list", "part")
"""What `<identification>` has to be inserted before, per the MusicXML order."""


def declare_explicit_layout(root: ET.Element) -> None:
    """Adds the `<supports>` declarations a MusiCorpus MusicXML file needs.

    A MusicXML document may either encode its system and page breaks or leave
    them to the renderer, and it says which in `identification/encoding`:

        <supports element="print" attribute="new-system" type="yes" value="yes"/>

    Without that declaration a reader cannot tell an absence of breaks from an
    absence of information, so `musicorpus validate` rejects a file that omits
    it. OLiMPiC files carry no `<identification>` at all, and they do not need
    to encode a break: each is one system on one page, so there is no break to
    encode and nothing left for a renderer to decide. The declaration says so.

    Modifies `root` in place and does nothing if the declarations are present.
    """
    identification = _find_or_insert(root, "identification", ELEMENTS_AFTER_IDENTIFICATION)
    encoding = _find_or_insert(identification, "encoding", ())

    for attribute in SUPPORTED_BREAK_ATTRIBUTES:
        if encoding.find(f'supports[@element="print"][@attribute="{attribute}"]') is not None:
            continue
        ET.SubElement(
            encoding,
            "supports",
            {"element": "print", "attribute": attribute, "type": "yes", "value": "yes"},
        )


def _find_or_insert(parent: ET.Element, tag: str, before_tags: tuple[str, ...]) -> ET.Element:
    """Returns `parent`'s child of `tag`, creating it in document order if absent."""
    existing = parent.find(tag)
    if existing is not None:
        return existing

    element = ET.Element(tag)
    for index, child in enumerate(parent):
        if child.tag in before_tags:
            parent.insert(index, element)
            return element
    parent.append(element)
    return element
