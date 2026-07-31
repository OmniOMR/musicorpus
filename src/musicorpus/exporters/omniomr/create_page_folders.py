import tqdm
from pathlib import Path


def create_page_folders(page_names: list[str], output_folder: Path):
    """Creates empty page folders in the output folder"""
    for page_name in tqdm.tqdm(page_names, "Creating page folders"):
        (output_folder / page_name).mkdir()
