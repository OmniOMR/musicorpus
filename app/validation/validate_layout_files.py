from pathlib import Path
from ..ErrorBag import ErrorBag
from ..MusicorpusManifest import MusicorpusManifest
import json
from .validate_coco_object_detection_file import validate_info_block, \
    validate_licenses, validate_images, validate_categories, validate_annotations


def validate_layout_file(
        dataset_path: Path,
        layout_file: Path,
        manifest: MusicorpusManifest,
        errors: ErrorBag
):
    relative_path = layout_file.relative_to(dataset_path)
    page_name = relative_path.parts[0]

    # load the raw JSON data
    with open(layout_file, "r") as f:
        data: dict = json.load(f)

    # get data parts
    data_info: dict = data.get("info", {})
    data_licenses: list[dict] = data.get("licenses", [])
    data_images: list[dict] = data.get("images", [])
    data_annotations: list[dict] = data.get("annotations", {})
    data_categories: list[dict] = data.get("categories", {})

    # validate the file by blocks
    validate_info_block(
        page_name=page_name,
        coco_file=layout_file,
        data_info=data_info,
        manifest=manifest,
        errors=errors
    )

    license_ids: set[int] = validate_licenses(
        dataset_path=dataset_path,
        page_name=page_name,
        coco_file=layout_file,
        data_licenses=data_licenses,
        errors=errors
    )

    image_ids: set[int] = validate_images(
        dataset_path=dataset_path,
        page_name=page_name,
        coco_file=layout_file,
        data_images=data_images,
        license_ids=license_ids,
        errors=errors
    )

    categories: dict[int, str] = validate_categories(
        page_name=page_name,
        coco_file=layout_file,
        data_categories=data_categories,
        errors=errors
    )

    validate_annotations(
        page_name=page_name,
        coco_file=layout_file,
        data_annotations=data_annotations,
        image_ids=image_ids,
        categories=categories,
        errors=errors
    )

    # validate categories whitelst
    whitelist = [
        "staff", "emptyStaff", "grandstaff", "system",
        "staffMeasure", "grandstaffMeasure", "systemMeasure"
    ]
    for category in categories.values():
        if category not in whitelist:
            errors.add_error(
                page_name=page_name,
                message=f"The layout.json file contains the category " +
                f"'{category}' which is not one of the allowed " +
                f"categories in this file {whitelist}. In: {layout_file}"
            )
