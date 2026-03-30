from pathlib import Path
from ..ErrorBag import ErrorBag
from mung.node import Node
from mung.graph import NotationGraph
from mung.io import read_nodes_from_file
from .InputLayoutFile import InputLayoutFile
from ..get_ordered_mung_staves import get_ordered_mung_staves
from ..get_ordered_mung_systems import get_ordered_mung_systems
import tqdm
from ..Layout import Layout
from ..CocoBbox import CocoBbox
from ..mung_to_coco import CocoLicense, CocoDatasetMetadata, CocoImageMetadata
from functools import reduce
from ..get_image_size import get_image_size


def create_layout_files(
        page_names: list[str],
        omniomr_layout_file: InputLayoutFile, # different "layout" file
        output_folder: Path,
        errors: ErrorBag,
        dataset_metadata: CocoDatasetMetadata,
        image_license: CocoLicense
):
    """Creates the layout.json file in each page folder"""
    for page_name in tqdm.tqdm(page_names, "Creating layout files"):
        
        # load MuNG file
        mung_path = output_folder / page_name / "transcription.mung"
        if not mung_path.exists():
            errors.add_error(
                page_name,
                "Computing layout.json - MuNG file missing at: " \
                    + str(mung_path)
            )
            continue
        mung_graph = NotationGraph(read_nodes_from_file(mung_path))

        # get omniomr layout record
        if page_name not in omniomr_layout_file.records:
            errors.add_error(
                page_name,
                "Computing layout.json - OmniOMR Layout record missing for the page."
            )
            continue
        omniomr_layout_record = omniomr_layout_file.records[page_name]

        # load image
        image_path = output_folder / page_name / "image.jpg"
        if not image_path.exists():
            errors.add_error(
                page_name,
                "image.jpg not found in: " + str(image_path)
            )
            continue
        image_width, image_height = get_image_size(image_path)

        # get all mung staves, sorted top-down
        mung_staves = get_ordered_mung_staves(mung_graph)

        # get all mung systems, sorted top-down
        mung_systems = get_ordered_mung_systems(mung_graph)

        def mung_node_to_coco_bbox(node: Node) -> CocoBbox:
            return CocoBbox(
                left=node.left,
                top=node.top,
                width=node.width,
                height=node.height
            )

        # prepare the layout file contents
        staves: list[CocoBbox] = []
        empty_staves: list[CocoBbox] = []
        grandstaves: list[CocoBbox] = []
        systems: list[CocoBbox] = []

        # build all staves and empty staves
        for i in range(1, len(mung_staves) + 1):
            staff = mung_node_to_coco_bbox(mung_staves[i - 1])
            if i in omniomr_layout_record.empty_staves:
                empty_staves.append(staff)
            else:
                staves.append(staff)
        
        # build all grandstaves
        for i, j in omniomr_layout_record.grandstaves:
            staff_i = mung_node_to_coco_bbox(mung_staves[i - 1])
            staff_j = mung_node_to_coco_bbox(mung_staves[j - 1])
            grandstaff = staff_i.union_with(staff_j)
            grandstaves.append(grandstaff)

        # build all systems
        for mung_system in mung_systems:
            system: CocoBbox = reduce(
                lambda x, y: x.union_with(y),
                [
                    mung_node_to_coco_bbox(mung_staff)
                    for mung_staff in mung_system
                ]
            )
            systems.append(system)

        # build the final layout file and write it
        layout = Layout(
            dataset_metadata=dataset_metadata,
            image_metadata=CocoImageMetadata(
                width=image_width,
                height=image_height,
                file_name=image_path.relative_to(output_folder).as_posix(),
                date_captured=dataset_metadata.date_created
            ),
            image_license=image_license,
            staves=staves,
            empty_staves=empty_staves,
            grandstaves=grandstaves,
            systems=systems,
            staff_measures=[], # TODO: measures not implemented
            grandstaff_measures=[],
            system_measures=[]
        )
        layout.write_to_file(output_folder / page_name / "layout.json")
