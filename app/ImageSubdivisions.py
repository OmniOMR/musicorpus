from dataclasses import dataclass, field
from pathlib import Path
from .CocoBbox import CocoBbox
import json


@dataclass
class ImageSubdivisions:
    """
    Represents the contents of the 'subdivisions.image.json' file,
    parsed into a dataclass to be easily accessible in python.
    """
    
    staves: dict[str, CocoBbox] = field(default_factory=dict)
    """Cropboxes for individual staves"""

    grandstaves: dict[str, CocoBbox] = field(default_factory=dict)
    """Cropboxes for individual grandstaves"""

    systems: dict[str, CocoBbox] = field(default_factory=dict)
    """Cropboxes for individual systems"""

    @staticmethod
    def load_from(file_path: Path) -> "ImageSubdivisions":
        with open(file_path, "r") as file:
            data = json.load(file)
        assert type(data) is dict

        staves = data.get("Staves", {})
        assert type(staves) is dict
        assert all(type(value) is dict for value in staves.values())

        grandstaves = data.get("Grandstaves", {})
        assert type(grandstaves) is dict
        assert all(type(value) is dict for value in grandstaves.values())

        systems = data.get("Systems", {})
        assert type(systems) is dict
        assert all(type(value) is dict for value in systems.values())

        return ImageSubdivisions(
            staves={
                name: CocoBbox.from_json(d.get("bbox"))
                for name, d in staves.items()
            },
            grandstaves={
                name: CocoBbox.from_json(d.get("bbox"))
                for name, d in grandstaves.items()
            },
            systems={
                name: CocoBbox.from_json(d.get("bbox"))
                for name, d in systems.items()
            }
        )

    def write_to(self, file_path: Path):
        """Writes the data to a 'subdivisions.image.json' file."""
        data = {
            "Staves": {
                name: {
                    "bbox": list(bbox)
                }
                for name, bbox in self.staves.items()
            },
            "Grandstaves": {
                name: {
                    "bbox": list(bbox)
                }
                for name, bbox in self.grandstaves.items()
            },
            "Systems": {
                name: {
                    "bbox": list(bbox)
                }
                for name, bbox in self.systems.items()
            }
        }
        
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)
