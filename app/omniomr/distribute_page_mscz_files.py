import tqdm
import shutil
from pathlib import Path
from ..ErrorBag import ErrorBag


def distribute_page_mscz_files(
        page_names: list[str],
        editions_folder: Path,
        output_folder: Path,
        errors: ErrorBag
):
    """
    Distributes MuseScore files from the MuseScore Editions folder
    to output page folders.
    """
    for page_name in tqdm.tqdm(page_names, "Distributing MuseScore files"):
        source_path = editions_folder / (page_name + ".mscz")
        target_path = output_folder / page_name / "transcription.mscz"

        if not source_path.exists():
            errors.add_error(
                page_name,
                "Source MuseScore file not found at: " \
                    + str(source_path)
            )
            continue

        shutil.copy(source_path, target_path)
