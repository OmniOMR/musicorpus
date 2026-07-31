from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class CocoStatistics:
    """Statistics for the coco-object-detection.json files"""

    count: int = 0
    """Number of coco files counted"""

    annotations: int = 0
    """Total number of COCO annotations (object instances)"""
    
    def to_yaml(self) -> dict:
        return {
            "count": self.count,
            "annotations": self.annotations,
        }

    def add_instace(self, subdivision_folder: Path):
        coco_path = subdivision_folder / "coco-object-detection.json"
        if not coco_path.exists():
            return
        
        # load the JSON file
        with open(coco_path, "r") as f:
            data = json.load(f)

        # update statistics
        self.count += 1
        self.annotations += len(data["annotations"])
