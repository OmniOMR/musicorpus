import tqdm
import shutil
from pathlib import Path
from ..ErrorBag import ErrorBag


def distribute_page_images(
        page_names: list[str],
        mung_studio_folder: Path,
        output_folder: Path,
        errors: ErrorBag
):
    """
    Distributes page images from MungStudio documents
    to output page folders. Assumes all pages are ".jpg"
    """
    for page_name in tqdm.tqdm(page_names, "Distributing page images"):
        source_path = mung_studio_folder / page_name / "image.jpg"
        target_path = output_folder / page_name / "image.jpg"

        if not source_path.exists():
            errors.add_error(
                page_name,
                "Source image not found in MungStudio documents at: " \
                    + str(source_path)
            )
            continue

        shutil.copy(source_path, target_path)
