import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class CocoBbox:
    """Class that represents a COCO-style bounding box.

    COCO bounding box is a quadruplet of integers [l, t, w, h]
    with values being left, top, width, height in pixels.
    """

    def __init__(self, left: int, top: int, width: int, height: int):
        self.left = int(left)
        self.top = int(top)
        self.width = int(width)
        self.height = int(height)

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def area(self) -> int:
        """Rectangular area of the bbox"""
        return self.width * self.height

    def coco_quadrangle(self) -> list[int]:
        """
        Returns a polygon that encapsulated this bbox
        (as a naive segmentation mask)
        """
        return [
            self.left,
            self.top,
            self.left,
            self.top + self.height,
            self.left + self.width,
            self.top + self.height,
            self.left + self.width,
            self.top,
        ]

    def __iter__(self):
        yield self.left
        yield self.top
        yield self.width
        yield self.height

    def __repr__(self):
        return f"CocoBbox({self.left}, {self.top}, {self.width}, {self.height})"

    @staticmethod
    def from_json(json) -> "CocoBbox":
        """Parses the COCO bbox from a JSON list, e.g. [1,2,3,4]"""
        assert isinstance(json, list)
        assert len(json) == 4
        return CocoBbox(*[int(i) for i in json])

    def dilate(self, amount: int) -> "CocoBbox":
        """Enlarges the bbox in all directions by the given amount"""
        return CocoBbox(
            left=self.left - amount,
            top=self.top - amount,
            width=self.width + 2 * amount,
            height=self.height + 2 * amount,
        )

    def intersect_with(self, other: "CocoBbox") -> "CocoBbox":
        """Intersects the bbox with another one and returns the result.
        Returns a 0-sized bbox if the two bboxes do not overlap."""
        left = max(self.left, other.left)
        right = min(self.right, other.right)
        width = max(0, right - left)

        top = max(self.top, other.top)
        bottom = min(self.bottom, other.bottom)
        height = max(0, bottom - top)

        return CocoBbox(left=left, top=top, width=width, height=height)

    def union_with(self, other: "CocoBbox") -> "CocoBbox":
        """Unions the bbox with another one and returns the result."""
        left = min(self.left, other.left)
        right = max(self.right, other.right)

        top = min(self.top, other.top)
        bottom = max(self.bottom, other.bottom)

        return CocoBbox(left=left, top=top, width=right - left, height=bottom - top)


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
        return [{"id": id, "name": name} for id, name in self._id_to_name.items()]


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
            json.dump({"mung_to_coco": self.mung_to_coco_ids_map}, f)
