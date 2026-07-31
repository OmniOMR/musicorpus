import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from .coco import CocoBbox, CocoCategoriesMap, CocoDatasetMetadata, CocoImageMetadata, CocoLicense


@dataclass
class Layout:
    """Represents the layout.json file"""

    # metadata
    dataset_metadata: CocoDatasetMetadata
    image_metadata: CocoImageMetadata
    image_license: CocoLicense

    # annotation bboxes
    staves: list[CocoBbox]
    empty_staves: list[CocoBbox]
    grandstaves: list[CocoBbox]
    systems: list[CocoBbox]
    staff_measures: list[CocoBbox]
    grandstaff_measures: list[CocoBbox]
    system_measures: list[CocoBbox]

    # Which annotation category each of the bbox lists above is stored under
    # in the COCO JSON. Reading and writing both go through this, so the two
    # cannot drift apart.
    CATEGORY_NAMES: ClassVar[dict[str, str]] = {
        "staves": "staff",
        "empty_staves": "emptyStaff",
        "grandstaves": "grandstaff",
        "systems": "system",
        "staff_measures": "staffMeasure",
        "grandstaff_measures": "grandstaffMeasure",
        "system_measures": "systemMeasure",
    }

    @staticmethod
    def load_from_file(file_path: Path) -> "Layout":
        with open(file_path) as f:
            data = json.load(f)
        return Layout.parse_from_json(data)

    @staticmethod
    def parse_from_json(data: dict) -> "Layout":
        """Parses the COCO JSON object that `serialize_to_json` produces."""
        info = data["info"]
        image = data["images"][0]
        license_data = data["licenses"][0]

        category_name_by_id: dict[int, str] = {
            int(category["id"]): str(category["name"]) for category in data["categories"]
        }

        bboxes_by_category: dict[str, list[CocoBbox]] = {
            name: [] for name in Layout.CATEGORY_NAMES.values()
        }
        for annotation in data["annotations"]:
            category_name = category_name_by_id[int(annotation["category_id"])]
            # a category this class does not model is skipped rather than
            # rejected, so that a layout.json carrying extra annotations
            # still reads
            if category_name in bboxes_by_category:
                bboxes_by_category[category_name].append(CocoBbox.from_json(annotation["bbox"]))

        return Layout(
            dataset_metadata=CocoDatasetMetadata(
                version=str(info["version"]),
                description=str(info["description"]),
                contributor=str(info["contributor"]),
                url=str(info["url"]),
                date_created=datetime.strptime(str(info["date_created"]), "%Y/%m/%d"),
            ),
            image_metadata=CocoImageMetadata(
                width=int(image["width"]),
                height=int(image["height"]),
                file_name=str(image["file_name"]),
                date_captured=datetime.strptime(str(image["date_captured"]), "%Y-%m-%d %H:%M:%S"),
            ),
            image_license=CocoLicense(name=str(license_data["name"]), url=str(license_data["url"])),
            **{
                field: bboxes_by_category[category_name]
                for field, category_name in Layout.CATEGORY_NAMES.items()
            },
        )

    def write_to_file(self, file_path: Path):
        data = self.serialize_to_json()
        with open(file_path, "w") as f:
            json.dump(data, f)

    def serialize_to_json(self) -> dict:
        """Serializes the contents into the COCO JSON object"""

        coco_json: dict = {}
        categories = CocoCategoriesMap()

        # === info ===

        coco_json["info"] = {
            "year": self.dataset_metadata.date_created.year,
            "version": self.dataset_metadata.version,
            "description": self.dataset_metadata.description,
            "contributor": self.dataset_metadata.contributor,
            "url": self.dataset_metadata.url,
            "date_created": self.dataset_metadata.date_created.strftime("%Y/%m/%d"),
        }

        # === licenses ===

        coco_json["licenses"] = [
            {"id": 0, "name": self.image_license.name, "url": self.image_license.url}
        ]

        # === images ===

        coco_json["images"] = [
            {
                "id": 0,
                "width": self.image_metadata.width,
                "height": self.image_metadata.height,
                "file_name": self.image_metadata.file_name,
                "license": 0,
                "date_captured": self.image_metadata.date_captured.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ]

        # === annotations ===

        annotations: list[dict] = []
        coco_id = 0

        def _bbox_to_annotation(bbox: CocoBbox, category_name: str) -> dict:
            nonlocal coco_id, categories
            return {
                "id": coco_id,
                "image_id": 0,
                "category_id": categories.get_id_of(category_name),
                "segmentation": [bbox.coco_quadrangle()],
                "area": bbox.area,
                "bbox": list(bbox),
                "iscrowd": 0,
            }

        for field, category_name in Layout.CATEGORY_NAMES.items():
            for bbox in getattr(self, field):
                annotations.append(_bbox_to_annotation(bbox, category_name))
                coco_id += 1

        coco_json["annotations"] = annotations

        # === categories ===

        coco_json["categories"] = categories.to_json()

        return coco_json
