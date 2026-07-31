from dataclasses import dataclass
from pathlib import Path


@dataclass
class MungStatistics:
    """Statistics for the transcription.mung files"""

    count: int = 0
    """Number of mung files counted"""

    nodes: int = 0
    """Total number of MuNG nodes"""
    
    def to_yaml(self) -> dict:
        return {
            "count": self.count,
            "nodes": self.nodes,
        }

    def add_instace(self, subdivision_folder: Path):
        mung_path = subdivision_folder / "transcription.mung"
        if not mung_path.exists():
            return
        
        # instead of parsing the file, simply process it as a string
        # since it's way faster as it doesn't need to decode RLE masks
        mung_string = mung_path.read_text("utf-8")

        # update statistics
        self.count += 1
        self.nodes += mung_string.count("</Node>")
