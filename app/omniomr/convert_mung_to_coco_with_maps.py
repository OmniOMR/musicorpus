import tqdm
from pathlib import Path
from ..ImageSubdivisions import ImageSubdivisions
from ..ErrorBag import ErrorBag
from mung.graph import NotationGraph
from mung.io import read_nodes_from_file
from ..mung_to_coco import mung_to_coco, CocoDatasetMetadata, \
    CocoLicense, CocoImageMetadata, CocoFromMung
from ..get_image_size import get_image_size
import traceback
import json


def convert_mung_to_coco_with_maps(
        page_names: list[str],
        output_folder: Path,
        errors: ErrorBag,
        dataset_metadata: CocoDatasetMetadata,
        image_license: CocoLicense
):
    """Converts all MuNG files for each page in all subdivisions to COCO files
    and also generates maps between COCO subdivision ids and MuNG-COCO IDs"""
    for page_name in tqdm.tqdm(page_names, "MuNG to COCO with maps"):
        
        # load subdivisions cropboxes
        subdivisions_path = output_folder / page_name / "subdivisions.image.json"
        if not subdivisions_path.exists():
            errors.add_error(
                page_name,
                "subdivisions.image.json not found in: " + str(subdivisions_path)
            )
            continue
        subdivisions = ImageSubdivisions.load_from(subdivisions_path)

        # all folders to be processed (page & subdivisions)
        # (first MUST be the page-level folder)
        folders_to_process: list[Path] = [
            output_folder / page_name
        ] + [
            output_folder / page_name / "Staves" / staff_name
            for staff_name in subdivisions.staves.keys()
        ] + [
            output_folder / page_name / "Grandstaves" / grandstaff_name
            for grandstaff_name in subdivisions.grandstaves.keys()
        ] + [
            output_folder / page_name / "Systems" / system_name
            for system_name in subdivisions.systems.keys()
        ]

        page_coco: CocoFromMung | None = None
        """COCO file at the page-level"""

        coco_subdivisions_map: dict = {
            "Staves": {},
            "Grandstaves": {},
            "Systems": {}
        }
        """Contents of the subdivisions.coco-object-detection.json file"""

        # === process each folder ===

        for folder in folders_to_process:

            # load image
            image_path = folder / "image.jpg"
            if not image_path.exists():
                errors.add_error(
                    page_name,
                    "image.jpg not found in: " + str(image_path)
                )
                continue
            image_width, image_height = get_image_size(image_path)

            # load mung
            mung_path = folder / "transcription.mung"
            if not mung_path.exists():
                errors.add_error(
                    page_name,
                    "transcription.mung not found in: " + str(mung_path)
                )
                continue
            try:
                mung_graph = NotationGraph(read_nodes_from_file(mung_path))
            except Exception:
                errors.add_error(
                    page_name,
                    "transcription.mung filed to load: " + traceback.format_exc()
                )
                continue

            # write COCO and the mung2coco map
            coco = mung_to_coco(
                mung_graph=mung_graph,
                dataset_metadata=dataset_metadata,
                image_license=image_license,
                image_metadata=CocoImageMetadata(
                    width=image_width,
                    height=image_height,
                    file_name=image_path.relative_to(output_folder).as_posix(),
                    date_captured=dataset_metadata.date_created
                )
            )
            coco.write_coco_to_file(
                folder / "coco-object-detection.json"
            )
            coco.write_mung_to_coco_map_to_file(
                folder / "mung-to-coco-ids-map.json"
            )

            # =================

            # the first run is the page-level
            if page_coco is None:
                page_coco = coco
                continue

            # now we are within some subdivision,
            # let's figure out in which by getting the path parts,
            # e.g. "Grandstaff" / "1-2"
            subdivision_type, subdivision_name = folder \
                .relative_to(output_folder / page_name) \
                .parts

            # compute the COCO2COCO map
            page_to_local_map: dict[int, int] = {
                page_coco.mung_to_coco_ids_map[mung_id]: local_coco_id
                for local_coco_id, mung_id in coco.coco_to_mung_ids_map.items()
            }

            # write the map into the subdivisions map
            coco_subdivisions_map[subdivision_type][subdivision_name] = {
                "page_to_local": page_to_local_map
            }
        
        # finally, write subdivisions.coco-object-detection.json
        with open(output_folder / page_name \
            / "subdivisions.coco-object-detection.json", "w") as f:
            json.dump(coco_subdivisions_map, f, indent=2)
