import tqdm
from pathlib import Path
from ..ErrorBag import ErrorBag
from .InputDpiFile import InputDpiFile


def distribute_page_mung_files(
        page_names: list[str],
        mung_studio_folder: Path,
        dpi_file: InputDpiFile,
        output_folder: Path,
        errors: ErrorBag,
        mung_dataset_name: str
):
    """
    Distributes page MuNG files from MungStudio documents
    to output page folders.
    """
    for page_name in tqdm.tqdm(page_names, "Distributing page MuNG files"):
        source_path = mung_studio_folder / page_name / "mung.xml"
        target_path = output_folder / page_name / "transcription.mung"

        if not source_path.exists():
            errors.add_error(
                page_name,
                "Source mung file not found in MungStudio documents at: " \
                    + str(source_path)
            )
            continue

        # copy the file over line-by-line
        with open(source_path, "r", encoding="utf-8") as source:
            with open(target_path, "w", encoding="utf-8") as target:
                for line in source:

                    # adjust the root node attributes
                    if line.startswith("<Nodes "):
                        line = '<Nodes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' + \
                            f'dataset="{mung_dataset_name}" ' + \
                            f'document="{page_name}" ' + \
                            f'dpi="{dpi_file.dpis[page_name]}" ' + \
                            'xsi:noNamespaceSchemaLocation="CVC-MUSCIMA_Schema.xsd">'

                    # otherwise just copy the line as-is
                    target.write(line)
