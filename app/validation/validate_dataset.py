from pathlib import Path
from ..ErrorBag import ErrorBag
from ..MusicorpusManifest import MusicorpusManifest
from ..Splits import Splits
import traceback


def validate_dataset(
        dataset_path: Path,
        errors: ErrorBag
):
    page_names_by_folders: list[str] = [
        f.name for f in dataset_path.iterdir()
        if f.is_dir()
    ]
    
    # === root ===

    # musicorpus-specification.pdf
    if not (dataset_path / "musicorpus-specification.pdf").exists():
        errors.add_error(
            page_name="root",
            message="The musicorpus-specification.pdf file is " +
                "recommended to be present in the dataset root."
        )
    
    # musicorpus.json
    if not (dataset_path / "musicorpus.json").exists():
        errors.add_error(
            page_name="root",
            message="The musicorpus.json file " +
                "must be present in the dataset root."
        )
        return # no more checking can be done without the manifest file
    manifest = MusicorpusManifest.load_from_file(
        dataset_path / "musicorpus.json"
    )
    # NOTE: no detailed validation of manifest values is performed,
    # only parsing is done, which will crash if fields are missing

    # dataset folder name
    expected_dataset_folder_name = (
        manifest.short_institution_name +
        "." + manifest.short_dataset_name
    )
    if dataset_path.name != expected_dataset_folder_name:
        errors.add_error(
            page_name="root",
            message=f"The dataset folder should be " +
            f"called {expected_dataset_folder_name} but instead " + 
            f"is called {dataset_path.name}"
        )
    
    # README.md
    if not (dataset_path / "README.md").exists():
        errors.add_error(
            page_name="root",
            message="The README.md file " +
                "must be present in the dataset root."
        )

    # LICENSE.txt
    if not (dataset_path / "LICENSE.txt").exists():
        errors.add_error(
            page_name="root",
            message="The LICENSE.txt file " +
                "must be present in the dataset root."
        )
    
    print(list(dataset_path.glob("splits.*.json")))

    # splits.json and splits.*.json
    splits_files = [dataset_path / "splits.json"] + \
        list(dataset_path.glob("splits.*.json"))
    for splits_file_path in splits_files:
        if not splits_file_path.exists():
            errors.add_error(
                page_name="root",
                message=f"The {splits_file_path.name} file " +
                    "must be present in the dataset root."
            )
        else:
            # these will crash if splits don't hold invariants
            try:
                splits = Splits.read_from_file(
                    file_path=splits_file_path,
                    run_assertions=True
                )
                splits.check_that_it_covers_page_names_exactly(
                    page_names_by_folders,
                    raise_on_failure=True
                )
            except:
                errors.add_error(
                    page_name="root",
                    message="The splits.json file has an issue:\n" +
                        traceback.format_exc()
                )

    # === pages ===

    # TODO: validate individual pages
