import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

import tqdm
from lmx.musicxml.io.write_musicxml_tree_to_file import write_musicxml_tree_to_file
from lmx.musicxml.layout.extract_grandstaff import extract_grandstaff
from lmx.musicxml.layout.extract_staff import extract_staff
from lmx.musicxml.layout.extract_system import extract_system
from lmx.musicxml.layout.MusicXmlLayoutMap import MusicXmlLayoutMap

from ...error_bag import ErrorBag
from ...image_subdivisions import ImageSubdivisions
from .input_layout_file import InputLayoutFile


def mung2mxl_staff_index(mung_staff_number: int, empty_staves: list[int]) -> int:
    """Converts MuNG 1-based staff number to 0-based MusicXML staff
    index within a page. MXL indexing skips non-system staves."""
    empty_staves_above = len([
        staff_number for staff_number in empty_staves
        if staff_number <= mung_staff_number
    ])
    mung_staff_index = mung_staff_number - 1 # to 0-based
    return mung_staff_index - empty_staves_above


def subdivide_musicxml_files(
        page_names: list[str],
        layout_file: InputLayoutFile,
        output_folder: Path,
        errors: ErrorBag
):
    """Crops page musicxml files into all of their subdivisions"""
    for page_name in tqdm.tqdm(page_names, "Subdividing musicxml files"):
        
        # load subdivisions cropboxes
        subdivisions_path = output_folder / page_name / "subdivisions.image.json"
        if not subdivisions_path.exists():
            errors.add_error(
                page_name,
                "subdivisions.image.json not found in: " + str(subdivisions_path)
            )
            continue
        subdivisions = ImageSubdivisions.load_from(subdivisions_path)

        # load page mung
        mung_path = output_folder / page_name / "transcription.mung"
        if not mung_path.exists():
            errors.add_error(
                page_name,
                "Page-level transcription.mung not found in: " + str(mung_path)
            )
            continue

        # get layout record
        if page_name not in layout_file.records:
            errors.add_error(
                page_name,
                "Layout record missing for the page."
            )
            continue
        layout_record = layout_file.records[page_name]

        # load page musicxml
        musicxml_tree: ET.ElementTree = ET.ElementTree(ET.fromstring(
            (output_folder / page_name / "transcription.musicxml")\
                .read_text("utf-8")
        ))
        musicxml_root = musicxml_tree.getroot()
        assert musicxml_root is not None
        assert musicxml_root.tag == "score-partwise"

        # parse musicxml layout (pages, systems, parts, staves)
        layout_map = MusicXmlLayoutMap(musicxml_tree)

        # === run assertions ===

        if layout_map.page_count != 1:
            errors.add_error(
                page_name,
                "MusicXML files must be single-page"
            )
            continue

        if layout_map.staff_count_on_page(0) + len(layout_record.empty_staves) \
            != layout_record.staff_count:
            errors.add_error(
                page_name,
                "MusicXML does not have matching staff count with MuNG"
            )
            continue

        # === crop subdivisions ===

        # staves
        for staff_name in subdivisions.staves:
            staff_number = int(staff_name)
            try:
                write_musicxml_tree_to_file(
                    (output_folder / page_name / "Staves"
                        / staff_name / "transcription.musicxml"),
                    extract_staff(
                        layout_map=layout_map,
                        staff_location=layout_map.locate_staff_from_page_staff_index(
                            page_index=0,
                            page_staff_index=mung2mxl_staff_index(
                                staff_number, layout_record.empty_staves
                            )
                        )
                    )
                )
            except Exception:
                errors.add_error(
                    page_name,
                    f"Problem cropping MusicXML for staff {staff_name}: {traceback.format_exc()}"
                )

        # grandstaves
        for grandstaff_name in subdivisions.grandstaves:
            staff_range = [int(num) for num in grandstaff_name.split("-")]
            try:
                write_musicxml_tree_to_file(
                    (output_folder / page_name / "Grandstaves"
                        / grandstaff_name / "transcription.musicxml"),
                    extract_grandstaff(
                        layout_map=layout_map,
                        upper_staff_location=layout_map.locate_staff_from_page_staff_index(
                            page_index=0,
                            page_staff_index=mung2mxl_staff_index(
                                staff_range[0], layout_record.empty_staves
                            )
                        ),
                        lower_staff_location=layout_map.locate_staff_from_page_staff_index(
                            page_index=0,
                            page_staff_index=mung2mxl_staff_index(
                                staff_range[1], layout_record.empty_staves
                            )
                        )
                    )
                )
            except Exception:
                errors.add_error(
                    page_name,
                    f"Problem cropping MusicXML for grandstaff "
                    f"{grandstaff_name}: {traceback.format_exc()}"
                )

        # systems
        for page_system_index, system_name in enumerate(subdivisions.systems.keys()):
            try:
                write_musicxml_tree_to_file(
                    (output_folder / page_name / "Systems"
                        / system_name / "transcription.musicxml"),
                    extract_system(
                        layout_map=layout_map,
                        page_index=0,
                        page_system_index=page_system_index
                    )
                )
            except Exception:
                errors.add_error(
                    page_name,
                    f"Problem cropping MusicXML for system {system_name}: {traceback.format_exc()}"
                )
