from dataclasses import dataclass, field
from pathlib import Path
from .ImageStatistics import ImageStatistics
from .MetadataStatistics import MetadataStatistics
from .CocoStatistics import CocoStatistics
from .MusicXmlStatistics import MusicXmlStatistics
from .MungStatistics import MungStatistics


@dataclass
class SubdivisionStatistics:
    """Statistics for one subdivision, including page-level"""

    count: int = 0
    """Number of folders of this subdivision level
    (i.e. number of pages, staves, grandstaves, systems)"""

    image: ImageStatistics = field(default_factory=ImageStatistics)
    metadata: MetadataStatistics = field(default_factory=MetadataStatistics)
    coco: CocoStatistics = field(default_factory=CocoStatistics)
    musicxml: MusicXmlStatistics = field(default_factory=MusicXmlStatistics)
    mung: MungStatistics = field(default_factory=MungStatistics)

    def to_yaml(self) -> dict:
        return {
            "count": self.count,
            "image": self.image.to_yaml(),
            "metadata": self.metadata.to_yaml(),
            "coco": self.coco.to_yaml(),
            "musicxml": self.musicxml.to_yaml(),
            "mung": self.mung.to_yaml()
        }

    def add_instance(self, subdivision_folder: Path):
        self.count += 1
        self.image.add_instance(subdivision_folder=subdivision_folder)
        self.metadata.add_instance(subdivision_folder=subdivision_folder)
        self.coco.add_instace(subdivision_folder=subdivision_folder)
        self.musicxml.add_instance(subdivision_folder=subdivision_folder)
        self.mung.add_instace(subdivision_folder=subdivision_folder)
