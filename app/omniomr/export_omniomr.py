from pathlib import Path
from ..ErrorBag import ErrorBag
from ..PageMetadata import PageMetadata
from ..MusicorpusManifest import MusicorpusManifest
from .InputLayoutFile import InputLayoutFile
from .InputDpiFile import InputDpiFile
from .create_page_folders import create_page_folders
from .distribute_page_images import distribute_page_images
from .distribute_page_mscz_files import distribute_page_mscz_files
from .distribute_page_mung_files import distribute_page_mung_files
from .distribute_page_metadata import distribute_page_metadata
from .create_layout_files import create_layout_files
from .convert_page_mscz_files_to_musicxml import convert_page_mscz_files_to_musicxml
from .compute_image_subdivisions_from_mung import compute_image_subdivisions_from_mung
from .create_subdivisions_folders import create_subdivisions_folders
from .subdivide_images import subdivide_images
from .subdivide_mung_files import subdivide_mung_files
from .subdivide_musicxml_files import subdivide_musicxml_files
from .convert_mung_to_coco_with_maps import convert_mung_to_coco_with_maps
from ..mung_to_coco import CocoDatasetMetadata, CocoLicense
from datetime import datetime
from ..Splits import Splits
import shutil


def export_omniomr(
        page_names: list[str],
        mung_studio_folder: Path,
        editions_folder: Path,
        page_metadatas: dict[str, PageMetadata],
        layout_file: InputLayoutFile,
        dpi_file: InputDpiFile,
        output_folder: Path,
):
    """Run the dataset export process (builds the dataset from our soruces)"""

    errors = ErrorBag()
    now = datetime.now()
    assets_folder = Path(__file__).parent / "assets"

    # === root ===

    # create the output folder
    output_folder.mkdir(parents=True)

    # musicorpus.json
    manifest = MusicorpusManifest.load_from_file(
        assets_folder / "musicorpus.json"
    )
    manifest.created_at = now
    manifest.write_to_file(output_folder / "musicorpus.json")

    # TODO: README.md

    # LICENSE.txt
    shutil.copy(
        assets_folder / "LICENSE.txt",
        output_folder / "LICENSE.txt"
    )

    # splits.json
    splits = Splits.read_from_file(assets_folder / "splits.json")
    splits.check_that_it_covers_page_names_exactly(page_names)
    splits.write_to_file(output_folder / "splits.json")
    
    # splits.book-consistent.json
    splits_bc = Splits.read_from_file(assets_folder / "splits.book-consistent.json")
    splits_bc.check_that_it_covers_page_names_exactly(page_names)
    splits_bc.write_to_file(output_folder / "splits.book-consistent.json")

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

    # metadata.json
    distribute_page_metadata(
        page_names=page_names,
        page_metadatas=page_metadatas,
        output_folder=output_folder,
        errors=errors
    )

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
        mung_dataset_name=manifest.full_dataset_name
    )

    # subdivisions.image.json
    compute_image_subdivisions_from_mung(
        page_names=page_names,
        layout_file=layout_file,
        output_folder=output_folder,
        errors=errors
    )

    # layout.json
    create_layout_files(
        page_names=page_names,
        omniomr_layout_file=layout_file,
        output_folder=output_folder,
        errors=errors,
        dataset_metadata=CocoDatasetMetadata(
            version=manifest.dataset_version,
            description=manifest.short_institution_name + \
                "." + manifest.short_dataset_name,
            contributor=manifest.full_institution_name,
            url=manifest.dataset_url,
            date_created=now
        ),
        image_license=CocoLicense(
            name="OmniOMR.UFAL/LICENSE.txt",
            url="musicorpus://OmniOMR.UFAL/LICENSE.txt"
        )
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
        mung_dataset_name=manifest.full_dataset_name
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
            version=manifest.dataset_version,
            description=manifest.short_institution_name + \
                "." + manifest.short_dataset_name,
            contributor=manifest.full_institution_name,
            url=manifest.dataset_url,
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
