from dataclasses import dataclass, field
from pathlib import Path
from .SubdivisionStatistics import SubdivisionStatistics


@dataclass
class SplitStatistics:
    """Statistics for one dataset split"""

    pages: SubdivisionStatistics = field(default_factory=SubdivisionStatistics)
    staves: SubdivisionStatistics = field(default_factory=SubdivisionStatistics)
    grandstaves: SubdivisionStatistics = field(default_factory=SubdivisionStatistics)
    systems: SubdivisionStatistics = field(default_factory=SubdivisionStatistics)
    
    def to_yaml(self) -> dict:
        return {
            "pages": self.pages.to_yaml(),
            "staves": self.staves.to_yaml(),
            "grandstaves": self.grandstaves.to_yaml(),
            "systems": self.systems.to_yaml(),
        }

    def add_page(self, dataset_path: Path, page_name: str):
        self.pages.add_instance(
            subdivision_folder=dataset_path / page_name
        )

        staves_folder = dataset_path / page_name / "Staves"
        grandstaves_folder = dataset_path / page_name / "Grandstaves"
        systems_folder = dataset_path / page_name / "Systems"

        if staves_folder.exists():
            for staff_folder in staves_folder.iterdir():
                self.staves.add_instance(
                    subdivision_folder=staff_folder
                )
        
        if grandstaves_folder.exists():
            for grandstaff_folder in grandstaves_folder.iterdir():
                self.grandstaves.add_instance(
                    subdivision_folder=grandstaff_folder
                )
        
        if systems_folder.exists():
            for system_folder in systems_folder.iterdir():
                self.systems.add_instance(
                    subdivision_folder=system_folder
                )
