from pathlib import Path, PosixPath
from ..ErrorBag import ErrorBag
import traceback
from ..get_image_size import get_image_size
from ..CocoBbox import CocoBbox
from ..MusicorpusManifest import MusicorpusManifest
import json
from datetime import datetime
from pycocotools.mask import frPyObjects


def validate_coco_object_detection_file(
        dataset_path: Path,
        coco_file: Path,
        manifest: MusicorpusManifest,
        errors: ErrorBag
):
    relative_path = coco_file.relative_to(dataset_path)
    page_name = relative_path.parts[0]

    # load the raw JSON data
    with open(coco_file, "r") as f:
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
        coco_file=coco_file,
        data_info=data_info,
        manifest=manifest,
        errors=errors
    )

    license_ids: set[int] = validate_licenses(
        dataset_path=dataset_path,
        page_name=page_name,
        coco_file=coco_file,
        data_licenses=data_licenses,
        errors=errors
    )

    image_ids: set[int] = validate_images(
        dataset_path=dataset_path,
        page_name=page_name,
        coco_file=coco_file,
        data_images=data_images,
        license_ids=license_ids,
        errors=errors
    )

    categories: dict[int, str] = validate_categories(
        page_name=page_name,
        coco_file=coco_file,
        data_categories=data_categories,
        errors=errors
    )

    validate_annotations(
        page_name=page_name,
        coco_file=coco_file,
        data_annotations=data_annotations,
        image_ids=image_ids,
        categories=categories,
        errors=errors
    )


def validate_info_block(
        page_name: str,
        coco_file: Path,
        data_info: dict,
        manifest: MusicorpusManifest,
        errors: ErrorBag
):
    data_year = int(data_info.get("year", 0))
    data_version = str(data_info.get("version"))
    data_description = str(data_info.get("description"))
    data_contributor = str(data_info.get("contributor"))
    data_url = str(data_info.get("url"))
    data_date_created = str(data_info.get("date_created"))

    # check field equivalency with the manifest

    if data_version != manifest.dataset_version:
        errors.add_error(
            page_name=page_name,
            message=f"The COCO file's 'info.version' ({data_version}) " +
            f"field must match the 'musicorpus.json/dataset_version' " +
            f"({manifest.dataset_version}) field. In: {coco_file}"
        )
    
    dataset_folder_name = manifest.short_institution_name + "." + manifest.short_dataset_name
    if data_description != dataset_folder_name:
        errors.add_error(
            page_name=page_name,
            message=f"The COCO file's 'info.description' ({data_description}) " +
            f"field must match the 'musicorpus.json/short_institution_name' " +
            "and 'musicorpus.json/short_dataset_name' " +
            f"({dataset_folder_name}) combined fields. In: {coco_file}"
        )
    
    if data_contributor != manifest.full_institution_name:
        errors.add_error(
            page_name=page_name,
            message=f"The COCO file's 'info.contributor' ({data_contributor}) " +
            f"field must match the 'musicorpus.json/full_institution_name' " +
            f"({manifest.full_institution_name}) field. In: {coco_file}"
        )
    
    if data_url != manifest.dataset_url:
        errors.add_error(
            page_name=page_name,
            message=f"The COCO file's 'info.url' ({data_url}) " +
            f"field must match the 'musicorpus.json/dataset_url' " +
            f"({manifest.dataset_url}) field. In: {coco_file}"
        )
    
    try:
        date_created = datetime.strptime(data_date_created, "%Y/%m/%d")
    except:
        errors.add_error(
            page_name=page_name,
            message=f"The COCO file's 'info.date_created' ({data_date_created}) " +
            f"field must be formatted as 'YYYY/MM/DD'. You can use the " +
            f"following code in python: `d = datetime.now(); " +
            f"d.strftime(\"%Y/%m/%d\")` In: {coco_file}" +
            traceback.format_exc()
        )
        return

    if data_year != date_created.year:
        errors.add_error(
            page_name=page_name,
            message=f"The COCO file's 'info.year' ({data_year}) " +
            f"field must match the 'info.date_created' " +
            f"({data_date_created}) field's year value. In: {coco_file}"
        )


def validate_licenses(
        dataset_path: Path,
        page_name: str,
        coco_file: Path,
        data_licenses: list[dict],
        errors: ErrorBag
) -> set[int]:
    license_ids = set()
    
    for i, data_license in enumerate(data_licenses):
        
        # parse ID
        if "id" not in data_license:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'licenses[{i}].id' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_id = int(data_license["id"])

        # remember the ID
        if data_id in license_ids:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'licenses[{i}].id' " +
                f"field is using a license ID ({data_id}) that was already " +
                f"defined by some other license in this COCO file. In: {coco_file}"
            )
        license_ids.add(data_id)
        
        # parse name
        if "name" not in data_license:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'licenses[{i}].name' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_name = str(data_license["name"])

        # parse url
        if "url" not in data_license:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'licenses[{i}].url' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_url = str(data_license["url"])

        # check musicorpus URLs
        schema = "musicorpus://"
        if data_url.lower().startswith(schema):
            path = PosixPath(data_url[len(schema):])
            full_path = dataset_path.parent / path
            if not full_path.is_file():
                errors.add_error(
                    page_name=page_name,
                    message=f"The COCO file's 'licenses[{i}].url' " +
                    f"field is {data_url} which references the " +
                    f"file {full_path}. However this file does not " +
                    f"exist. Make sure the referenced license is part " +
                    f"of the dataset. In: {coco_file}"
                )

    return license_ids


def validate_images(
        dataset_path: Path,
        page_name: str,
        coco_file: Path,
        data_images: list[dict],
        license_ids: set[int],
        errors: ErrorBag
) -> set[int]:
    image_ids = set()
    
    for i, data_image in enumerate(data_images):
        
        # parse ID
        if "id" not in data_image:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].id' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_id = int(data_image["id"])

        # remember the ID
        if data_id in image_ids:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].id' " +
                f"field is using an image ID ({data_id}) that was already " +
                f"defined by some other image in this COCO file. In: {coco_file}"
            )
        image_ids.add(data_id)

        # parse width
        if "width" not in data_image:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].width' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_width = int(data_image["width"])

        # parse height
        if "height" not in data_image:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].height' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_height = int(data_image["height"])

        # parse file_name
        if "file_name" not in data_image:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].file_name' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_file_name = str(data_image["file_name"])

        # check referenced image exists
        image_path = dataset_path / PosixPath(data_file_name)
        if not image_path.is_file():
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].file_name' " +
                f"field references the file {image_path}, but that " +
                f"file does not exist. In: {coco_file}"
            )

        # verify image size
        if image_path.is_file():
            w, h = get_image_size(image_path)
            if w != data_width or h != data_height:
                errors.add_error(
                    page_name=page_name,
                    message=f"The COCO file's 'images[{i}]' " +
                    f"specified width and height ({data_width}, {data_height}) " +
                    "does not match the size of the referenced file ({w}, {h})" +
                    f"In: {coco_file}"
                )

        # parse license ID
        if "license" not in data_image:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].license' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_license = int(data_image["license"])

        # verify license exists
        if data_license not in license_ids:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'images[{i}].license' " +
                f"field references ID {data_license}, but this " +
                f"license ID is not defined in the licenses block. " +
                f"In: {coco_file}"
            )

    return image_ids


def validate_categories(
        page_name: str,
        coco_file: Path,
        data_categories: list[dict],
        errors: ErrorBag
):
    categories: dict[int, str] = {}

    for i, data_category in enumerate(data_categories):
        
        # parse ID
        if "id" not in data_category:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'categories[{i}].id' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_id = int(data_category["id"])

        # parse name
        if "name" not in data_category:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'categories[{i}].name' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_name = str(data_category["name"])

        # remember the category
        if data_id in categories:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'categories[{i}].id' " +
                f"field is using a category ID ({data_id}) that was already " +
                f"defined by some other category ({categories[data_id]}) in this COCO file. In: {coco_file}"
            )
        categories[data_id] = data_name

    return categories


def validate_annotations(
        page_name: str,
        coco_file: Path,
        data_annotations: list[dict],
        image_ids: set[int],
        categories: dict[int, str],
        errors: ErrorBag
) -> set[int]:
    annotation_ids: set[int] = set()

    for i, data_annotation in enumerate(data_annotations):
        
        # parse ID
        if "id" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].id' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_id = int(data_annotation["id"])

        # remember the ID
        if data_id in annotation_ids:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].id' " +
                f"field is using an annotation ID ({data_id}) that was already " +
                f"defined by some other annotation in this COCO file. In: {coco_file}"
            )
        annotation_ids.add(data_id)

        # parse image ID
        if "image_id" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].image_id' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_image_id = int(data_annotation["image_id"])

        # verify image exists
        if data_image_id not in image_ids:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].image_id' " +
                f"field references ID {data_image_id}, but this " +
                f"image ID is not defined in the images block. " +
                f"In: {coco_file}"
            )
        
        # parse category ID
        if "category_id" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].category_id' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_category_id = int(data_annotation["category_id"])

        # verify category exists
        if data_category_id not in categories:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].category_id' " +
                f"field references ID {data_category_id}, but this " +
                f"category ID is not defined in the categories block. " +
                f"In: {coco_file}"
            )
        
        # parse iscrowd
        if "iscrowd" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].iscrowd' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        data_iscrowd = int(data_annotation["iscrowd"])
        
        # verify iscrowd is 0
        if data_iscrowd != 0:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].iscrowd' " +
                f"field must be 0, since we are annotating music " +
                f"notation glyph instances. In: {coco_file}"
            )

        # check bbox exists
        if "bbox" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].bbox' " +
                f"field is missing. In: {coco_file}"
            )
            continue

        # verify bbox is parsable
        try:
            data_bbox = CocoBbox.from_json(data_annotation["bbox"])
        except:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].bbox' " +
                f"field is not parsable. In: {coco_file}\n" +
                traceback.format_exc()
            )

        # check segmentation exists
        if "segmentation" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].segmentation' " +
                f"field is missing. In: {coco_file}"
            )
            continue
        
        # check segmentation is parsable
        try:
            data_segmentation = data_annotation["segmentation"]
            if type(data_segmentation) in [list, dict]:
                frPyObjects(
                    pyobj=data_segmentation,
                    h=data_bbox.height,
                    w=data_bbox.width
                )
            else:
                raise ValueError(
                    "Segmentation must be a list (polygons) or dict (RLE). " +
                    "See the MusiCorpus specification for more."
                )
        except:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].segmentation' " +
                f"field is not parsable. In: {coco_file}\n" +
                traceback.format_exc()
            )

        # check area exists
        if "area" not in data_annotation:
            errors.add_error(
                page_name=page_name,
                message=f"The COCO file's 'annotations[{i}].area' " +
                f"field is missing. In: {coco_file}"
            )
        
        # NOTE: We're not checking that the area value is computed properly,
        # because rounding errors and implementation differences may lead
        # to unexpected false-positives. Such validation would be more
        # harm than good.

    return annotation_ids
