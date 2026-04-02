from dataclasses import dataclass, field
from pathlib import Path
from ..get_image_size import get_image_size
from statistics import median, mean, stdev


@dataclass
class ImageStatistics:
    """Statistics for image.jpg files"""
    
    widths: list[int] = field(default_factory=list)
    """Widths of all images"""

    heights: list[int] = field(default_factory=list)
    """Heights of all images"""
    
    def to_yaml(self) -> dict:
        assert len(self.widths) == len(self.heights)
        return {
            "count": len(self.widths),
            "width": {
                "mean": mean(self.widths),
                "stdev": stdev(self.widths),
                "median": median(self.widths),
                "min": min(self.widths),
                "max": max(self.widths),
            },
            "height": {
                "mean": mean(self.heights),
                "stdev": stdev(self.heights),
                "median": median(self.heights),
                "min": min(self.heights),
                "max": max(self.heights),
            },
        }

    def add_instance(self, subdivision_folder: Path):
        image_path = subdivision_folder / "image.jpg"
        if not image_path.exists():
            return
        
        width, height = get_image_size(image_path)
        self.widths.append(width)
        self.heights.append(height)
