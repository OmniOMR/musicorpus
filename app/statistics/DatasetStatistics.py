from dataclasses import dataclass, field
from .SplitStatistics import SplitStatistics
from pathlib import Path
from ..Splits import Splits


@dataclass
class DatasetStatistics:
    """Complete statistics object for a MusiCorpus dataset"""
    
    dataset_name: str
    """Human-readable name of the dataset to include in the stats yaml"""

    whole_dataset: SplitStatistics = field(default_factory=SplitStatistics)
    """Aggregate statistics for the whole dataset"""

    splits_statistics: dict[str, SplitStatistics] = field(default_factory=dict)
    """Statistics aggregated only over individual splits"""

    def to_yaml(self) -> dict:
        return {
            "NAME": self.dataset_name,
            "WHOLE_DATASET": self.whole_dataset.to_yaml(),
            "SPLITS": {
                split_name: split_statistics.to_yaml()
                for split_name, split_statistics
                in self.splits_statistics.items()
            }
        }
    
    def add_page(self, dataset_path: Path, page_name: str, splits: Splits):
        self.whole_dataset.add_page(
            dataset_path=dataset_path,
            page_name=page_name
        )
        for split_name in splits.split_names():
            if page_name in splits[split_name]:
                # insert into this split
                if split_name not in self.splits_statistics:
                    self.splits_statistics[split_name] = SplitStatistics()
                self.splits_statistics[split_name].add_page(
                    dataset_path=dataset_path,
                    page_name=page_name
                )
