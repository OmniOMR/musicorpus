from mung.graph import NotationGraph
from .CocoBbox import CocoBbox
from dataclasses import dataclass
from pycocotools.mask import area, frPyObjects
import numpy as np
from datetime import datetime
from pathlib import Path
import json


def encode_coco_rle_mask(mask: np.ndarray) -> dict:
    """Converts a 2D uint8 bitmap to COCO uncompressed RLE mask"""
    assert len(mask.shape) == 2
    counts = []
    last_element: int = 0
    running_length: int = 0

    for i, element in enumerate(mask.ravel(order="F")):
        if element != 0:
            element = 1
        if element != last_element:
            counts.append(running_length)
            running_length = 0
            last_element = element
        running_length += 1

    counts.append(running_length)

    return {
        "size": list(mask.shape),
        "counts": counts
    }


@dataclass(frozen=True)
class CocoDatasetMetadata:
    version: str
    """Version of the dataset"""

    description: str
    """Name of the musicorpus dataset"""

    contributor: str
    """Name of the institution or individual behind the dataset"""

    url: str
    """URL link to a website about the dataset or project"""

    date_created: datetime
    """Date when the dataset was created"""


@dataclass(frozen=True)
class CocoLicense:
    name: str
    """Human-readable name of the license"""

    url: str
    """URL link to the license body"""


@dataclass(frozen=True)
class CocoImageMetadata:
    width: int
    """Width of the image in pixels"""

    height: int
    """Height of the image in pixels"""

    file_name: str
    """Posix path (forward slashes) from the root of 
    the dataset to the image file"""

    date_captured: datetime
    """Timestamp when the image file was first created.
    If unavailable, it can be set to the creation time of the dataset."""


class CocoCategoriesMap:
    """Mapping from COCO category IDs to category names"""
    def __init__(self) -> None:
        self._id_to_name: dict[int, str] = {}
        self._name_to_id: dict[str, int] = {}
        self._next_id = 0
    
    def get_id_of(self, name: str) -> int:
        """Returns ID of a category by name, if new, assigns new ID"""
        if name not in self._name_to_id:
            self._name_to_id[name] = self._next_id
            self._id_to_name[self._next_id] = name
            self._next_id += 1
        
        return self._name_to_id[name]

    def get_name_of(self, id: int) -> str:
        """Returns name of the category by ID, the category must exist"""
        if id not in self._id_to_name:
            raise KeyError(f"Given category {id} does not exist in the map")
        return self._id_to_name[id]
    
    def to_json(self) -> list[dict]:
        """Exports the map into the COCO file format"""
        return [
            { "id": id, "name": name }
            for id, name in self._id_to_name.items()
        ]


@dataclass(frozen=True)
class CocoFromMung:
    """COCO data created from MuNG notation graph"""
    
    coco_json: dict
    """The COCO JSON data represented as python dictionaries"""

    mung_to_coco_ids_map: dict[int, int]
    """Mapping from MuNG node IDs to COCO annotation object IDs"""

    coco_to_mung_ids_map: dict[int, int]
    """Mapping from COCO annotation object IDs to MuNG node IDs"""

    def write_coco_to_file(self, file_path: Path):
        with open(file_path, "w") as f:
            json.dump(self.coco_json, f)
    
    def write_mung_to_coco_map_to_file(self, file_path: Path):
        with open(file_path, "w") as f:
            json.dump({
                "mung_to_coco": self.mung_to_coco_ids_map
            }, f)


def mung_to_coco(
        mung_graph: NotationGraph,
        dataset_metadata: CocoDatasetMetadata,
        image_license: CocoLicense,
        image_metadata: CocoImageMetadata
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
        "date_created": dataset_metadata.date_created \
            .strftime("%Y/%m/%d")
    }

    # === licenses ===

    coco_json["licenses"] = [
        {
            "id": 0,
            "name": image_license.name,
            "url": image_license.url
        }
    ]

    # === images ===

    coco_json["images"] = [
        {
            "id": 0,
            "width": image_metadata.width,
            "height": image_metadata.height,
            "file_name": image_metadata.file_name,
            "license": 0,
            "date_captured": image_metadata.date_captured \
                .strftime("%Y-%m-%d %H:%M:%S")
        }
    ]

    # === annotations ===

    annotations: list[dict] = []

    for coco_id, node in enumerate(mung_graph.vertices):
        seg = encode_coco_rle_mask(node.mask)
        seg_area = int(area(frPyObjects(seg, seg["size"][0], seg["size"][1])))
        annotations.append({
            "id": coco_id,
            "image_id": 0,
            "category_id": categories.get_id_of(node.class_name),
            "segmentation": seg,
            "area": seg_area,
            "bbox": list(CocoBbox(
                left=node.left,
                top=node.top,
                width=node.width,
                height=node.height
            )),
            "iscrowd": 0
        })

        # object ID mapping
        mung_to_coco_ids_map[node.id] = coco_id
        coco_to_mung_ids_map[coco_id] = node.id

    coco_json["annotations"] = annotations

    # === categories ===

    coco_json["categories"] = categories.to_json()

    return CocoFromMung(
        coco_json=coco_json,
        mung_to_coco_ids_map=mung_to_coco_ids_map,
        coco_to_mung_ids_map=coco_to_mung_ids_map
    )
