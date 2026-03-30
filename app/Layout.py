from dataclasses import dataclass
from .CocoBbox import CocoBbox
from .mung_to_coco import CocoDatasetMetadata, CocoImageMetadata, \
    CocoLicense, CocoCategoriesMap
import json
from pathlib import Path


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
            "date_created": self.dataset_metadata.date_created \
                .strftime("%Y/%m/%d")
        }

        # === licenses ===

        coco_json["licenses"] = [
            {
                "id": 0,
                "name": self.image_license.name,
                "url": self.image_license.url
            }
        ]

        # === images ===

        coco_json["images"] = [
            {
                "id": 0,
                "width": self.image_metadata.width,
                "height": self.image_metadata.height,
                "file_name": self.image_metadata.file_name,
                "license": 0,
                "date_captured": self.image_metadata.date_captured \
                    .strftime("%Y-%m-%d %H:%M:%S")
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
                "iscrowd": 0
            }

        for staff in self.staves:
            annotations.append(_bbox_to_annotation(staff, "staff"))
            coco_id += 1
        
        for empty_staff in self.empty_staves:
            annotations.append(_bbox_to_annotation(empty_staff, "emptyStaff"))
            coco_id += 1
        
        for grandstaff in self.grandstaves:
            annotations.append(_bbox_to_annotation(grandstaff, "grandstaff"))
            coco_id += 1
        
        for system in self.systems:
            annotations.append(_bbox_to_annotation(system, "system"))
            coco_id += 1
        
        for staff_measure in self.staff_measures:
            annotations.append(_bbox_to_annotation(staff_measure, "staffMeasure"))
            coco_id += 1
        
        for grandstaff_measure in self.grandstaff_measures:
            annotations.append(_bbox_to_annotation(grandstaff_measure, "grandstaffMeasure"))
            coco_id += 1

        for system_measure in self.system_measures:
            annotations.append(_bbox_to_annotation(system_measure, "systemMeasure"))
            coco_id += 1

        coco_json["annotations"] = annotations

        # === categories ===

        coco_json["categories"] = categories.to_json()

        return coco_json
