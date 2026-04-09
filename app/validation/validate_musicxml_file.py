from pathlib import Path
from ..ErrorBag import ErrorBag
import xml.etree.ElementTree as ET
import traceback
from ..musicxml.MusicXmlLayoutMap import MusicXmlLayoutMap


def validate_musicxml_file(
        dataset_path: Path,
        musicxml_file: Path,
        errors: ErrorBag
):
    relative_path = musicxml_file.relative_to(dataset_path)
    page_name = relative_path.parts[0]
    is_subdivision = len(relative_path.parts) > 2
    
    # load the MusicXML file
    try:
        musicxml_tree: ET.ElementTree = ET.ElementTree(ET.fromstring(
            musicxml_file.read_text("utf-8")
        ))
        assert musicxml_tree.getroot().tag == "score-partwise", \
            "The MusicXML file must have <score-partwise> in the root."
    except:
        errors.add_error(
            page_name=page_name,
            message=f"The file {musicxml_file} cannot be loaded:\n" +
                traceback.format_exc()
        )
        return

    # === layout assertions ===

    # parse musicxml layout (pages, systems, parts, staves)
    try:
        layout_map = MusicXmlLayoutMap(musicxml_tree)
    except:
        errors.add_error(
            page_name=page_name,
            message=f"Failed to load MusicXML layout for file {musicxml_file}:\n" +
                traceback.format_exc()
        )
        return

    if layout_map.page_count != 1:
        errors.add_error(
            page_name=page_name,
            message=f"MusicXML files must be single-page. " +
            f"File: {musicxml_file}"
        )
    
    if is_subdivision and layout_map.system_count != 1:
        errors.add_error(
            page_name=page_name,
            message=f"MusicXML files for page subdivisions " +
            f"must be single-system. The file has " +
            f"{layout_map.system_count} systems. File: {musicxml_file}"
        )

    # === page systems subdivisions ===

    # TODO: check that the number of systems matches systems subdivision
