from pathlib import Path
from .DatasetStatistics import DatasetStatistics
from ..Splits import Splits
import tqdm


def compute_statistics(
        dataset_path: Path,
        splits_file_name: str
) -> DatasetStatistics:
    """Computes statistics for a given MusiCorpus dataset"""
    
    # load the splits.json file
    splits = Splits.read_from_file(dataset_path / splits_file_name)
    
    statistics = DatasetStatistics(
        dataset_name=dataset_path.name
    )
    
    for page_name in tqdm.tqdm(
        splits.get_all_page_names(),
        "Aggregating statistics"
    ):
        statistics.add_page(
            dataset_path=dataset_path,
            page_name=page_name,
            splits=splits
        )

    return statistics
