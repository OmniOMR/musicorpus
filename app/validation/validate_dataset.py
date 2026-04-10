from pathlib import Path
from ..ErrorBag import ErrorBag
from ..MusicorpusManifest import MusicorpusManifest
from ..Splits import Splits
import traceback
from .check_folders_contain_files import check_folders_contain_files
from .validate_musicxml_file import validate_musicxml_file
from .validate_mung_file import validate_mung_file
from .validate_metadata_file import validate_metadata_file
from .validate_image_subdivisions_file import validate_image_subdivisions_file
from .validate_coco_object_detection_file import validate_coco_object_detection_file
from .validate_layout_files import validate_layout_file
import tqdm


def validate_dataset(
        dataset_path: Path,
        errors: ErrorBag
):
    page_names_by_folders: list[str] = [
        f.name for f in dataset_path.iterdir()
        if f.is_dir()
    ]
    
    # === root ===

    print("Checking dataset root files...")

    # musicorpus-specification.pdf
    print("Checking musicorpus-specification.pdf file...")
    if not (dataset_path / "musicorpus-specification.pdf").exists():
        errors.add_error(
            page_name="root",
            message="The musicorpus-specification.pdf file is " +
                "recommended to be present in the dataset root."
        )
    
    # musicorpus.json
    print("Checking musicorpus.json file...")
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
    print("Checking dataset folder name...")
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
    print("Checking README.md file...")
    if not (dataset_path / "README.md").exists():
        errors.add_error(
            page_name="root",
            message="The README.md file " +
                "must be present in the dataset root."
        )

    # LICENSE.txt
    print("Checking LICENSE.txt file...")
    if not (dataset_path / "LICENSE.txt").exists():
        errors.add_error(
            page_name="root",
            message="The LICENSE.txt file " +
                "must be present in the dataset root."
        )
    
    # splits.json and splits.*.json
    splits_files = [dataset_path / "splits.json"] + \
        list(dataset_path.glob("splits.*.json"))
    for splits_file_path in splits_files:
        print("Checking", splits_file_path.name, "file...")
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
                    message=f"The {splits_file_path.name} file has an issue:\n" +
                        traceback.format_exc()
                )

    # === folder homogeneity ===

    print("Checking that folders are homogenous...")

    page_folders = [f for f in dataset_path.iterdir() if f.is_dir()]
    staff_folders = list(dataset_path.glob("*/Staves/*"))
    grandstaff_folders = list(dataset_path.glob("*/Grandstaves/*"))
    system_folders = list(dataset_path.glob("*/Systems/*"))

    page_files: set[str] = set(
        file.name for page in page_folders
        for file in page.iterdir() if file.is_file()
    )
    staff_files: set[str] = set(
        file.name for staff in staff_folders
        for file in staff.iterdir() if file.is_file()
    )
    grandstaff_files: set[str] = set(
        file.name for grandstaff in grandstaff_folders
        for file in grandstaff.iterdir() if file.is_file()
    )
    system_files: set[str] = set(
        file.name for system in system_folders
        for file in system.iterdir() if file.is_file()
    )
    subdivisions_files = staff_files.union(grandstaff_files).union(system_files)
    all_files = page_files.union(subdivisions_files)

    print("Page files:", page_files)
    print("Staff files:", staff_files)
    print("Grandstaff files:", grandstaff_files)
    print("System files:", system_files)

    check_folders_contain_files(
        folders=page_folders,
        files=page_files,
        errors=errors,
        page_name_resolver=lambda folder: folder.name
    )
    check_folders_contain_files(
        folders=staff_folders,
        files=staff_files,
        errors=errors,
        page_name_resolver=lambda folder: folder.parent.parent.name
    )
    check_folders_contain_files(
        folders=grandstaff_folders,
        files=grandstaff_files,
        errors=errors,
        page_name_resolver=lambda folder: folder.parent.parent.name
    )
    check_folders_contain_files(
        folders=system_folders,
        files=system_files,
        errors=errors,
        page_name_resolver=lambda folder: folder.parent.parent.name
    )
    
    # === blacklisted files ===

    print("Checking blacklisted files...")

    if "image.jpeg" in all_files:
        errors.add_error(
            page_name="unknown",
            message="Dataset contains 'image.jpeg' files, " +
            "but they should really be called 'image.jpg' " +
            "instead (jpg != jpEg)."
        )
    
    if "transcription.mxl" in all_files:
        errors.add_error(
            page_name="unknown",
            message="Dataset contains 'transcription.mxl' files, " +
            "but they should really be 'transcription.musicxml' " +
            "instead. MusiCorpus requires uncompressed MusicXML files."
        )
    
    if "transcription.xml" in all_files:
        errors.add_error(
            page_name="unknown",
            message="Dataset contains 'transcription.xml' files, " +
            "but they should really be 'transcription.musicxml' " +
            "instead."
        )
    
    if "transcription.kern" in all_files:
        errors.add_error(
            page_name="unknown",
            message="Dataset contains 'transcription.kern' files, " +
            "but they should really be 'transcription.krn' " +
            "instead."
        )
    
    if "metadata.json" in subdivisions_files:
        errors.add_error(
            page_name="unknown",
            message="Dataset contains 'metadata.json' files in subdivision " +
            "folders. These represent page-level data and should only be " +
            "present in page folders."
        )

    # === validating individual file types ===

    # subdivisions.image.json
    for image_subdivisions_file in tqdm.tqdm(
        list(dataset_path.glob("**/subdivisions.image.json")),
        "Validating subdivisions.image.json files"
    ):
        validate_image_subdivisions_file(
            dataset_path=dataset_path,
            image_subdivisions_file=image_subdivisions_file,
            errors=errors
        )

    # metadata.json
    for metadata_file in tqdm.tqdm(
        list(dataset_path.glob("**/metadata.json")),
        "Validating metadata.json files"
    ):
        validate_metadata_file(
            dataset_path=dataset_path,
            metadata_file=metadata_file,
            errors=errors
        )
    
    # coco-object-detection.json
    for coco_file in tqdm.tqdm(
        list(dataset_path.glob("**/coco-object-detection.json")),
        "Validating coco-object-detection.json files"
    ):
        validate_coco_object_detection_file(
            dataset_path=dataset_path,
            coco_file=coco_file,
            manifest=manifest,
            errors=errors
        )

    # layout.json
    for layout_file in tqdm.tqdm(
        list(dataset_path.glob("**/layout.json")),
        "Validating layout.json files"
    ):
        validate_layout_file(
            dataset_path=dataset_path,
            layout_file=layout_file,
            manifest=manifest,
            errors=errors
        )

    # transcription.musicxml
    for musicxml_file in tqdm.tqdm(
        list(dataset_path.glob("**/transcription.musicxml")),
        "Validating transcription.musicxml files"
    ):
        validate_musicxml_file(
            dataset_path=dataset_path,
            musicxml_file=musicxml_file,
            errors=errors
        )

    # transcription.mung
    for mung_file in tqdm.tqdm(
        list(dataset_path.glob("**/transcription.mung")),
        "Validating transcription.mung files"
    ):
        validate_mung_file(
            dataset_path=dataset_path,
            mung_file=mung_file,
            errors=errors
        )
