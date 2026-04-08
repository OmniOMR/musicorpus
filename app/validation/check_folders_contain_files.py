from pathlib import Path
from ..ErrorBag import ErrorBag
from typing import Callable
import tqdm


def check_folders_contain_files(
        folders: list[Path],
        files: set[str],
        errors: ErrorBag,
        page_name_resolver: Callable[[Path], str]
):
    """Checks that given folders contain given filenames"""
    for folder in tqdm.tqdm(folders, "Checking folders for files"):
        page_name = page_name_resolver(folder)
        for file in files:
            if not (folder / file).is_file():
                errors.add_error(
                    page_name=page_name,
                    message=f"Missing {file} in {folder}"
                )
