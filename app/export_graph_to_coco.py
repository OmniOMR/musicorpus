import json
from typing import Optional, Any
from datetime import datetime
from pathlib import Path
from mung.graph import Node
from mung.io import read_nodes_from_file
from dataclasses import dataclass


COCO_EXPORT_LOGGING = True

@dataclass(frozen=True)
class COCORecord:
    page_name: str
    image_path: Path
    mung_path: Path
    image_width: int
    image_height: int


class COCOExporter:
    def __init__(self) -> None:
        self._records: list[COCORecord] = []

    def register_record(self, rec: COCORecord) -> None:
        self._records.append(rec)

    def export(
        self,
        output_path: str | Path,
        dataset_info: Optional[dict] = None,
        per_image_layout: bool = True,
        indent: int = 0
    ) -> None:
        """
        Export all registered pages into a single COCO JSON file.

        Categories are derived from the union of all class names across
        all pages. Image IDs and annotation IDs are globally unique.

        If `per_image_layout` is true, `layout.json` file is created
        for each image, this file contains image annotations in COCO
        format only from this image. All IDs in this file are globally
        unique a consistent with the global COCO JSON.

        :param output_path: Full path (including filename) of the output JSON file.
        :param dataset_info: Optional dict merged into the top-level ``info`` block.
            Recognized keys mirror the COCO standard: ``description``,
            ``url``, ``version``, ``year``, ``contributor``.

        Example
        -------
        >>> exporter = COCOExporter()
        >>> exporter.register_record(COCORecord(...))
        >>> exporter.export("out/dataset.json")
        """

        if COCO_EXPORT_LOGGING:
            print(f"Exporting COCO to {output_path} for {len(self._records)} records ...")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read all nodes upfront so we can build a global category map
        all_page_nodes: list[tuple[COCORecord, list[Node]]] = [
            (rec, read_nodes_from_file(str(rec.mung_path)))
            for rec in self._records
        ]

        # Global categories
        all_class_names = sorted({
            node.class_name
            for _, nodes in all_page_nodes
            for node in nodes
        })
        category_id_map = {name: i for i, name in enumerate(all_class_names)}
        categories = [
            {"id": cid, "name": name}
            for name, cid in category_id_map.items()
        ]
        
        # Info block (shared between images)
        info = {
            "description": "",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "",
            "date_created": datetime.now().strftime("%Y/%m/%d"),
        }
        if dataset_info:
            info.update(dataset_info)

        # Images and annotations
        images: list[dict[str, Any]] = []
        annotations: list[dict[str, Any]] = []
        ann_id = 0

        for image_id, (rec, nodes) in enumerate(all_page_nodes):
            if COCO_EXPORT_LOGGING:
                print(f"{image_id + 1}/{len(self._records)} Exporting COCO {rec.page_name}")
            image_details: dict[str, Any] = {
                "id": image_id,
                "file_name": rec.page_name,
                "width": rec.image_width,
                "height": rec.image_height,
                "date_captured": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            } 
            images.append(image_details)

            image_annotations: list[dict[str, Any]] = []
            for node in nodes:
                image_annotations.append({
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": category_id_map[node.class_name],
                    "bbox": [node.left, node.top, node.width, node.height],
                    "area": float(node.width * node.height),
                    "segmentation": [],
                    "iscrowd": 0,
                })
                ann_id += 1
            
            annotations.extend(image_annotations)

            # Create coco-object-detection.json for a single image file
            if per_image_layout:
                image_coco = {
                    "info": info,
                    "licenses": [],
                    "images": [image_details],
                    "annotations": image_annotations,
                    "categories": categories,
                }
                layout_path = rec.mung_path.parent / "coco-object-detection.json"
                with open(layout_path, "w") as f:
                    json.dump(image_coco, f, indent=indent)


        # Disabled the top-level file:
        # coco = {
        #     "info": info,
        #     "licenses": [],
        #     "images": images,
        #     "annotations": annotations,
        #     "categories": categories,
        # }

        # with open(output_path, "w") as f:
        #     json.dump(coco, f, indent=indent)
