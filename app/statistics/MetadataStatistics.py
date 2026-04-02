from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
from ..PageMetadata import PageMetadata


@dataclass
class MetadataStatistics:
    """Statistics for metadata.json files"""
    
    count: int = 0
    """Total number of metadata files found"""

    notation: Counter[str] = field(default_factory=Counter)
    notation_complexity: Counter[str] = field(default_factory=Counter)
    production: Counter[str] = field(default_factory=Counter)
    clarity: Counter[str] = field(default_factory=Counter)
    systems: Counter[str] = field(default_factory=Counter)
    
    def to_yaml(self) -> dict | None:
        if self.count == 0:
            return None
        
        return {
            "count": self.count,
            "notation": dict(self.notation.most_common()),
            "notation_complexity": dict(self.notation_complexity.most_common()),
            "production": dict(self.production.most_common()),
            "clarity": dict(self.clarity.most_common()),
            "systems": dict(self.systems.most_common())
        }

    def add_instance(self, subdivision_folder: Path):
        metadata_path = subdivision_folder / "metadata.json"
        if not metadata_path.exists():
            return
        
        metadata = PageMetadata.load_from_file(metadata_path)
        self.count += 1
        self.notation.update({ str(metadata.notation): 1 })
        self.notation_complexity.update({ str(metadata.notation_complexity): 1 })
        self.production.update({ str(metadata.production): 1 })
        self.clarity.update({ str(metadata.clarity): 1 })
        self.systems.update({ str(metadata.systems): 1 })
