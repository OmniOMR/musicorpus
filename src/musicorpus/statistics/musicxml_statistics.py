from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class MusicXmlStatistics:
    """Statistics for transcription.musicxml files"""
    
    count: int = 0
    """Number of musicxml files counted"""

    measures: int = 0
    """Total number of found measures (system measures)"""

    notes: int = 0
    """Total number of found <note> elements, which includes rests"""
    
    def to_yaml(self) -> dict:
        return {
            "count": self.count,
            "measures": self.measures,
            "notes": self.notes
        }

    def add_instance(self, subdivision_folder: Path):
        musicxml_path = subdivision_folder / "transcription.musicxml"
        if not musicxml_path.exists():
            return
        
        # load musicxml
        musicxml_tree: ET.ElementTree = ET.ElementTree(ET.fromstring(
            musicxml_path.read_text("utf-8")
        ))
        assert musicxml_tree.getroot().tag == "score-partwise"
        
        self.count += 1
        self._add_measures(musicxml_tree)
        self._add_notes(musicxml_tree)
    
    def _add_measures(self, musicxml_tree: ET.ElementTree):
        # find any part element (all should have the same number of measures)
        part_element = musicxml_tree.find("part")
        if part_element is None:
            return
        
        # count measures in that part
        self.measures += len(part_element.findall("measure"))

    def _add_notes(self, musicxml_tree: ET.ElementTree):
        for part_element in musicxml_tree.findall("part"):
            for measure_element in part_element.findall("measure"):
                for note_element in measure_element.findall("note"):
                    self.notes += 1
