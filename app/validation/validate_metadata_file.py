from pathlib import Path
from ..ErrorBag import ErrorBag
from ..PageMetadata import PageMetadata, NotationType, \
    NotationComplexity, NotationClarity, SystemsComposition, \
    ProductionType
import traceback
import json
from typing import get_args, Any


def validate_metadata_file(
        dataset_path: Path,
        metadata_file: Path,
        errors: ErrorBag
):
    relative_path = metadata_file.relative_to(dataset_path)
    page_name = relative_path.parts[0]
    is_subdivision = len(relative_path.parts) > 2
    
    # load the raw JSON
    with open(metadata_file, "r") as f:
        data: dict = json.load(f)
    
    # === check field types ===

    def _check_field_type(field_name: str, possible_types: list[Any]):
        nonlocal errors, data
        
        field_type: Any = "MISSING_FIELD"
        if field_name in data:
            field_type = type(data[field_name])
            if data[field_name] is False:
                field_type = False
            elif data[field_name] is None:
                field_type = None

        if field_type not in possible_types:
            errors.add_error(
                page_name=page_name,
                message=f"In metadata.json file, the field {field_name} " +
                f"has type {repr(field_type)}, which is not one of the " +
                f"allowed types {repr(possible_types)}. The file: {metadata_file}"
            )

    _check_field_type("file_name", [str])
    _check_field_type("institution_name", [str, False])
    _check_field_type("institution_rism_siglum", [str, None, False])
    _check_field_type("institution_local_siglum", [str, False])
    _check_field_type("shelfmark", [str, None, False])
    _check_field_type("rism_id_number", [str, None, False])
    _check_field_type("date", [str, None])
    _check_field_type("page_number", [int, str, None])
    _check_field_type("page_size", [list, None])
    _check_field_type("dpi", [int, None])
    _check_field_type("scribal_data", [int, str, None])
    _check_field_type("link", [str, None])
    _check_field_type("title_description", [str, None, False])
    _check_field_type("author", [str, None, False])
    _check_field_type("author_date", [str, None, False])
    _check_field_type("genre_form", [str, None])
    _check_field_type("notation", [str])
    _check_field_type("notation_detailed", [str, None])
    _check_field_type("production", [str])
    _check_field_type("production_detailed", [str, None])
    _check_field_type("notation_complexity", [str])
    _check_field_type("clarity", [str])
    _check_field_type("systems", [str])

    # === check field values ===

    def _check_field_value(field_name: str, possible_values: tuple | list):
        nonlocal errors, data
        
        field_value = data.get(field_name)

        if field_value not in possible_values:
            errors.add_error(
                page_name=page_name,
                message=f"In metadata.json file, the field {field_name} " +
                f"has value {repr(field_value)}, which is not one of the " +
                f"allowed values {repr(possible_values)}. The file: {metadata_file}"
            )
    
    _check_field_value("file_name", [
        (metadata_file.parent / "image.jpg")
            .relative_to(dataset_path)
            .as_posix()
    ])
    _check_field_value("notation", get_args(NotationType))
    _check_field_value("production", get_args(ProductionType))
    _check_field_value("notation_complexity", get_args(NotationComplexity))
    _check_field_value("clarity", get_args(NotationClarity))
    _check_field_value("systems", get_args(SystemsComposition))

    # === try parsing the file ===

    try:
        metadata = PageMetadata.load_from_file(metadata_file)
    except:
        errors.add_error(
            page_name=page_name,
            message=f"The file {metadata_file} cannot be loaded:\n" +
                traceback.format_exc()
        )
        return
