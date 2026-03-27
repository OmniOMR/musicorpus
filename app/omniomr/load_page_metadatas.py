from ..PageMetadata import PageMetadata
from .InputDpiFile import InputDpiFile
from pathlib import Path
import csv
import logging


# (so far there are no changes, but may be added in the future)
CSV_TO_MUSICORPUS_FIELD_MAP: dict[str, str] = {
    "institution_name": "institution_name",
    "institution_rism_siglum": "institution_rism_siglum",
    "instituion_local_siglum": "institution_local_siglum", # typo in the sheet
    "shelfmark": "shelfmark",
    "rism_id_number": "rism_id_number",
    "date": "date",
    "page_number": "page_number",
    "page_size": "page_size",
    "scribal_data": "scribal_data",
    "link": "link",
    "title_description": "title_description",
    "author": "author",
    "author_date": "author_date",
    "genre_form": "genre_form",
    "notation": "notation",
    "notation_detailed": "notation_detailed",
    "notation_complexity": "notation_complexity",
    "production": "production",
    "production_detailed": "production_detailed",
    "clarity": "clarity",
    "systems": "systems"
}


def load_page_metadatas(
        metadata_file_path: Path,
        dpi_file: InputDpiFile
) -> dict[str, PageMetadata]:
    """
    Loads page metadatas for OmniOMR from its CSV file.
    
    Returns a dictionary, where keys are page names
    and values are PageMetadata objects.
    """
    
    # read the CSV
    with open(metadata_file_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # turn it into a dictionary of records, one for each page
    page_metadatas: dict[str, PageMetadata] = {}

    for row in rows:
        # map the row field names to musicorpus json names
        json_data = {
            CSV_TO_MUSICORPUS_FIELD_MAP.get(key, key): value
            for key, value in row.items()
        }
        
        # empty string becomes null
        json_data = {
            key: "null" if value == "" else value
            for key, value in json_data.items()
        }

        # "null" becomes None
        json_data = {
            key: None if type(value) is str and value.lower() == "null" else value
            for key, value in json_data.items()
        }

        # "false" becomes False
        json_data = {
            key: False if type(value) is str and value.lower() == "false" else value
            for key, value in json_data.items()
        }

        # rows not assigned to a page are ignored
        if json_data["file_name"] in [None, ""]:
            continue

        # prepare page name and file name
        page_name = json_data["file_name"].removesuffix(".jpg")
        json_data["file_name"] = "UFAL.OmniOMR/" + page_name + "/image.jpg"
        
        # fix up messy page sizes
        if json_data["page_size"] is not None:
            json_data["page_size"] = process_page_size(json_data["page_size"])

        # unparsable dates are None
        try:
            int(json_data["date"])
        except ValueError:
            json_data["date"] = None

        # set DPI
        json_data["dpi"] = dpi_file.dpis.get(page_name, None)

        # parse the JSON
        page_metadatas[page_name] = PageMetadata \
            .parse_from_json(json_data)

    return page_metadatas


def process_page_size(page_size_string):
    """Converts the string representation of page size (e.g. "[200, 240]") into an actual tuple of integers.
    Note that there are many variations of uncertainty. While the strings should always look like "[200, 400]",
    often there are question marks where the dimension cannot be determined. In that case, we mark question
    marks as None.
    """
    result = None
    try:
        # If the string is well-formed and the dimensions are known.
        result = eval(page_size_string)

        "3, 4"
        if isinstance(result, tuple) and len(result) == 2:
            return result

        "[3, 4]"
        if isinstance(result, list) and len(result) == 2:
            result = tuple(result)
            return result

    except SyntaxError:
        logging.debug(f"Could not parse page size string '{page_size_string}' as a list of two integers.")
        pass
    except TypeError:
        logging.debug(f"Could not parse page size string '{page_size_string}' as a list of two integers.")
        pass
    except NameError:
        logging.debug(f"Could not parse page size string '{page_size_string}' as a list of two integers.")
        pass

    # Situations where we couldn't just eval to a tuple or list.
    if not page_size_string.startswith("[") or not page_size_string.endswith("]"):
        logging.debug(f"Page size string '{page_size_string}' does not start with '[' and end with ']'."
                        f" Cannot make parsing attempt.")
        return None

    if "," not in page_size_string:
        logging.debug(f"Page size string '{page_size_string}' does not contain a comma separating the dimensions.")
        return None

    # Try to split the string and parse the dimensions separately, marking any question marks as None.
    try:
        dimensions = page_size_string[1:-1].split(",")  # Account for [ and ]
        if len(dimensions) != 2:
            logging.debug(f"Page size string '{page_size_string}' does not contain exactly two dimensions separated by a comma.")
            return None

        width_str, height_str = dimensions
        width = int(width_str.strip()) if width_str.strip() != "?" else None
        height = int(height_str.strip()) if height_str.strip() != "?" else None

        result = (width, height)
        return result
    except Exception as e:
        logging.debug(f"An error occurred while parsing page size string '{page_size_string}': {e}")
        return None
