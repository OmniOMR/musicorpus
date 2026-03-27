import tqdm
import shutil
from pathlib import Path
from ..PageMetadata import PageMetadata
from ..ErrorBag import ErrorBag


def distribute_page_metadata(
        page_names: list[str],
        page_metadatas: dict[str, PageMetadata],
        output_folder: Path,
        errors: ErrorBag
):
    """
    Distributes page metadata into page-level metadata.json files.
    """
    for page_name in tqdm.tqdm(page_names, "Distributing page metadata"):

        # check that we have metadata available
        if page_name not in page_metadatas:
            errors.add_error(
                page_name,
                "Page metadata missing in the input metadata CSV."
            )
            continue

        # write the file
        page_metadatas[page_name].write_to_file(
            output_folder / page_name / "metadata.json"
        )
