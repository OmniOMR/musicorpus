import numpy as np
from mung.graph import NotationGraph
from pycocotools.mask import area, frPyObjects

from .coco import (
    CocoBbox,
    CocoCategoriesMap,
    CocoDatasetMetadata,
    CocoFromMung,
    CocoImageMetadata,
    CocoLicense,
)


def encode_coco_rle_mask(mask: np.ndarray) -> dict:
    """Converts a 2D uint8 bitmap to COCO uncompressed RLE mask"""
    assert len(mask.shape) == 2
    counts = []
    last_element: int = 0
    running_length: int = 0

    for element in mask.ravel(order="F"):
        if element != 0:
            element = 1
        if element != last_element:
            counts.append(running_length)
            running_length = 0
            last_element = element
        running_length += 1

    counts.append(running_length)

    return {"size": list(mask.shape), "counts": counts}


def mung_to_coco(
    mung_graph: NotationGraph,
    dataset_metadata: CocoDatasetMetadata,
    image_license: CocoLicense,
    image_metadata: CocoImageMetadata,
) -> CocoFromMung:
    """
    Converts a MuNG file into a COCO file JSON
    and returns that JSON in the form of python dictionaries.
    It also returns two maps between object coco IDs and mung IDs"""
    coco_json: dict = {}
    mung_to_coco_ids_map: dict[int, int] = {}
    coco_to_mung_ids_map: dict[int, int] = {}
    categories = CocoCategoriesMap()

    # === info ===

    coco_json["info"] = {
        "year": dataset_metadata.date_created.year,
        "version": dataset_metadata.version,
        "description": dataset_metadata.description,
        "contributor": dataset_metadata.contributor,
        "url": dataset_metadata.url,
        "date_created": dataset_metadata.date_created.strftime("%Y/%m/%d"),
    }

    # === licenses ===

    coco_json["licenses"] = [{"id": 0, "name": image_license.name, "url": image_license.url}]

    # === images ===

    coco_json["images"] = [
        {
            "id": 0,
            "width": image_metadata.width,
            "height": image_metadata.height,
            "file_name": image_metadata.file_name,
            "license": 0,
            "date_captured": image_metadata.date_captured.strftime("%Y-%m-%d %H:%M:%S"),
        }
    ]

    # === annotations ===

    annotations: list[dict] = []

    for coco_id, node in enumerate(mung_graph.vertices):
        seg = encode_coco_rle_mask(node.mask)
        seg_area = int(area(frPyObjects(seg, seg["size"][0], seg["size"][1])))
        annotations.append(
            {
                "id": coco_id,
                "image_id": 0,
                "category_id": categories.get_id_of(node.class_name),
                "segmentation": seg,
                "area": seg_area,
                "bbox": list(
                    CocoBbox(left=node.left, top=node.top, width=node.width, height=node.height)
                ),
                "iscrowd": 0,
            }
        )

        # object ID mapping
        mung_to_coco_ids_map[node.id] = coco_id
        coco_to_mung_ids_map[coco_id] = node.id

    coco_json["annotations"] = annotations

    # === categories ===

    coco_json["categories"] = categories.to_json()

    return CocoFromMung(
        coco_json=coco_json,
        mung_to_coco_ids_map=mung_to_coco_ids_map,
        coco_to_mung_ids_map=coco_to_mung_ids_map,
    )
