from pathlib import Path
from ..ErrorBag import ErrorBag
from .InputLayoutFile import InputLayoutFile
from .InputDpiFile import InputDpiFile
from .create_page_folders import create_page_folders
from .distribute_page_images import distribute_page_images
from .distribute_page_mscz_files import distribute_page_mscz_files
from .distribute_page_mung_files import distribute_page_mung_files
from .convert_page_mscz_files_to_musicxml import convert_page_mscz_files_to_musicxml
from .compute_image_subdivisions_from_mung import compute_image_subdivisions_from_mung
from .create_subdivisions_folders import create_subdivisions_folders
from .subdivide_images import subdivide_images
from .subdivide_mung_files import subdivide_mung_files
from .subdivide_musicxml_files import subdivide_musicxml_files
from .convert_mung_to_coco_with_maps import convert_mung_to_coco_with_maps
from ..mung_to_coco import CocoDatasetMetadata, CocoLicense
from datetime import datetime


def export_omniomr(
        page_names: list[str],
        mung_studio_folder: Path,
        editions_folder: Path,
        metadata: list[dict[str, str]],
        layout_file: InputLayoutFile,
        dpi_file: InputDpiFile,
        output_folder: Path,
):
    """Run the dataset export process (builds the dataset from our soruces)"""
    
    errors = ErrorBag()

    now = datetime.now()

    # === root ===

    # create the output folder
    output_folder.mkdir(parents=True)
    
    mung_dataset_name = "OmniOMR"

    # TODO: musicorpus.json

    # TODO: README.md

    # TODO: LICENSE.txt

    # TODO: splits.json

    # === pages ===

    create_page_folders(
        page_names=page_names,
        output_folder=output_folder
    )

    # image.jpg
    distribute_page_images(
        page_names=page_names,
        mung_studio_folder=mung_studio_folder,
        output_folder=output_folder,
        errors=errors
    )

    # TODO: metadata.json

    # TODO: layout.json

    # transcription.mscz
    distribute_page_mscz_files(
        page_names=page_names,
        editions_folder=editions_folder,
        output_folder=output_folder,
        errors=errors
    )

    # transcription.musicxml
    convert_page_mscz_files_to_musicxml(
        page_names=page_names,
        output_folder=output_folder,
        errors=errors
    )

    # transcription.mung
    distribute_page_mung_files(
        page_names=page_names,
        mung_studio_folder=mung_studio_folder,
        dpi_file=dpi_file,
        output_folder=output_folder,
        errors=errors,
        mung_dataset_name=mung_dataset_name
    )

    # subdivisions.image.json
    compute_image_subdivisions_from_mung(
        page_names=page_names,
        layout_file=layout_file,
        output_folder=output_folder,
        errors=errors
    )

    # === all subdivisions at once ===
    
    create_subdivisions_folders(
        page_names=page_names,
        output_folder=output_folder,
        errors=errors
    )

    # image.jpg
    subdivide_images(
        page_names=page_names,
        output_folder=output_folder,
        errors=errors
    )

    # transcription.mung
    subdivide_mung_files(
        page_names=page_names,
        output_folder=output_folder,
        errors=errors,
        mung_dataset_name=mung_dataset_name
    )

    # transcription.musicxml
    subdivide_musicxml_files(
        page_names=page_names,
        layout_file=layout_file,
        output_folder=output_folder,
        errors=errors
    )

    # === COCO universe ===

    # coco-object-detection.json
    # mung-to-coco-ids-map.json
    # subdivisions.coco-object-detection.json
    convert_mung_to_coco_with_maps(
        page_names=page_names,
        output_folder=output_folder,
        errors=errors,
        dataset_metadata=CocoDatasetMetadata(
            version="?", # TODO: fill this out
            description="?",
            contributor="?",
            url="?",
            date_created=now
        ),
        image_license=CocoLicense(
            name="OmniOMR.UFAL/LICENSE.txt",
            url="musicorpus://OmniOMR.UFAL/LICENSE.txt"
        )
    )
    
    # === finalize ===

    errors.write_report_if_any_errors(
        file_path=output_folder / "ERRORS.txt"
    )

    return

    # prepare metadata mapping from page name to metadata dict for page-wise export
    # metadata_per_page = prepare_metadata_per_page(
    #     metadata=metadata,
    #     page_names=page_names
    # )

    # Run optimally stratified split finding (brute-force, takes a few minutes for 100 pages with 10^6 iterations)
    # N_RANDOM_SPLITS = 10000  # 10^4 for testing, but use 10^6 samples for live run. It takes approx. 5 mins on M2 CPU.
    # SPLIT_FILE = output_folder / "dataset_splits.json"
    # STRICT_SPLIT_FILE = output_folder / "dataset_splits_STRICT.json"
    # best_split, best_stratification = find_best_random_split(metadata_per_page,
    #                                                          page_names,
    #                                                          allow_book_overlap=True,  # Permissive: books can repeat across splits
    #                                                          n_splits=N_RANDOM_SPLITS)
    # strict_best_split, strict_best_stratification = find_best_random_split(metadata_per_page,
    #                                                                        page_names,
    #                                                                        allow_book_overlap=False,  # Strict
    #                                                                        n_splits=N_RANDOM_SPLITS)
    # output_split_to_json(best_split, SPLIT_FILE)
    # output_split_to_json(strict_best_split, STRICT_SPLIT_FILE)
