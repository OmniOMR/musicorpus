import tqdm
from pathlib import Path
from ..ErrorBag import ErrorBag
from ..CocoBbox import CocoBbox
from ..ImageSubdivisions import ImageSubdivisions
from ..get_image_size import get_image_size
from ..HiddenPrints import HiddenPrints
from .InputLayoutFile import InputLayoutFile
from mung.graph import NotationGraph
from mung.io import read_nodes_from_file
from functools import reduce
from itertools import chain
from ..get_ordered_mung_staves import get_ordered_mung_staves
from ..get_ordered_mung_systems import get_ordered_mung_systems


def compute_image_subdivisions_from_mung(
        page_names: list[str],
        layout_file: InputLayoutFile,
        output_folder: Path,
        errors: ErrorBag
):
    """For each page, inspects its MuNG file and computes subdivision bboxes"""
    for page_name in tqdm.tqdm(page_names, "Computing image subdivisions"):
        
        # load MuNG file
        mung_path = output_folder / page_name / "transcription.mung"
        if not mung_path.exists():
            errors.add_error(
                page_name,
                "Computing subdivisions - MuNG file missing at: " \
                    + str(mung_path)
            )
            continue
        mung_graph = NotationGraph(read_nodes_from_file(mung_path))
        
        # get layout record
        if page_name not in layout_file.records:
            errors.add_error(
                page_name,
                "Computing subdivisions - Layout record missing for the page."
            )
            continue
        layout_record = layout_file.records[page_name]

        # get all mung staves, sorted top-down
        mung_staves = get_ordered_mung_staves(mung_graph)

        # verify that the staff count matches
        if len(mung_staves) != layout_record.staff_count:
            errors.add_error(
                page_name,
                f"Mung staff count ({len(mung_staves)}) does not match " + \
                f"layout data staff count ({layout_record.staff_count})."
            )
            continue

        # get all mung systems, sorted top-down
        mung_systems = get_ordered_mung_systems(mung_graph)

        # verify all systems are of the same size
        if len(set(len(system) for system in mung_systems)) != 1:
            errors.add_error(
                page_name,
                f"MuNG-detected systems do not have equal number of staves."
            )
            continue

        # get average staff height (from the mask, not bbox)
        staff_height: int = int(sum(
            staff.mask.sum(axis=0).mean()
            for staff in mung_staves
        ) / len(mung_staves))

        # get staff numbers that contain true pianoform music
        pianoform_staves = list(chain(*layout_record.true_pianoform_staves))

        # get the size of the page
        page_bbox = CocoBbox(
            0,
            0,
            *get_image_size(output_folder / page_name / "image.jpg")
        )

        # prepare the subdivisions file
        subdivisions = ImageSubdivisions()

        # build all staves
        for i in range(1, len(mung_staves) + 1):
            # skip empty staves
            if i in layout_record.empty_staves:
                continue
            # skip staves in true pianoform grandstaves
            if i in pianoform_staves:
                continue
            staff = mung_staves[i - 1]
            bbox = CocoBbox(staff.left, staff.top, staff.width, staff.height)
            cropbox = bbox.dilate(staff_height).intersect_with(page_bbox)
            subdivisions.staves[str(i)] = cropbox
        
        # build all grandstaves
        for i, j in layout_record.grandstaves:
            staff_i = mung_staves[i - 1]
            staff_j = mung_staves[j - 1]
            bbox_i = CocoBbox(staff_i.left, staff_i.top, staff_i.width, staff_i.height)
            bbox_j = CocoBbox(staff_j.left, staff_j.top, staff_j.width, staff_j.height)
            bbox = bbox_i.union_with(bbox_j)
            cropbox = bbox.dilate(staff_height).intersect_with(page_bbox)
            subdivisions.grandstaves[str(i) + "-" + str(j)] = cropbox

        # build all systems
        for system in mung_systems:
            staff_numbers = [
                mung_staves.index(staff) + 1
                for staff in system
            ]
            i = min(staff_numbers)
            j = max(staff_numbers)
            bbox = reduce(
                lambda x, y: x.union_with(y),
                [
                    CocoBbox(staff.left, staff.top, staff.width, staff.height)
                    for staff in system
                ]
            )
            cropbox = bbox.dilate(staff_height).intersect_with(page_bbox)
            subdivisions.systems[str(i) + "-" + str(j)] = cropbox

        # write the subdivisions file
        subdivisions.write_to(
            output_folder / page_name / "subdivisions.image.json"
        )
