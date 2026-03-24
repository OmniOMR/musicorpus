#!/usr/bin/env python
"""This is a script that loads MusiCorpus-style metadata from a CSV file,
validates it, and outputs a subset of it for the pages in our dataset,
formated in the expected JSON entries.

Can be also run as a standalone script. For use in perform_dataset_export.py,
two entry points are important:

- `prepare_metadata_per_page()`: takes the loaded metadata and prepares it for export per page,
  including normalisation and validation. It returns a dictionary mapping page names to their metadata dictionaries.
- `find_best_random_split()`: takes the prepared metadata and a list of page names, and finds a random split
  of the pages into train, val, and test subsets that is optimally stratified according to the metadata categories
  with controlled vocabularies. It returns the best split found and its stratification score.
"""

import argparse
import logging
import os
import pprint
import time
import csv
import json
import numpy as np

from pathlib import Path


__version__ = "0.0.1"
__author__ = "Jan Hajic jr."

# Example row from Google Sheet export:
# 99ad2b5f-0270-46c8-b00e-a773dc2291f0_89710f4b-3e69-4ffc-a2c3-6f846d758917.jpg,omr-annotation-training,---,,Moravian Library,CZ-Bu,MZK,RKPMus-0579.915,sources/553014026,1858,179,"[200, 240]","manuscript copy, copyist: Lepičovský, Josef F. (19th century)",https://www.digitalniknihovna.cz/mzk/view/uuid:99ad2b5f-0270-46c8-b00e-a773dc2291f0?page=uuid:89710f4b-3e69-4ffc-a2c3-6f846d758917,"Theresienmesse in B flat major, Hob XXII:12 ","Haydn, Joseph",1732-1809,mass,CWMN,,polyphonic,handwritten,null,sufficient,multi-instrument


# Each metadata record must have these fields. Some of them can be null, but they must be present.
METADATA_DEFINED_FIELDS = [
    "file_name",
    "institution_name", "institution_rism_siglum", "instituion_local_siglum", "shelfmark", "rism_id_number",
    "date", "page_number", "page_size", "scribal_data",
    "link",
    "title_description", "author", "author_date", "genre_form",
    "notation", "notation_detailed", "production", "production_detailed", "notation_complexity", "clarity", "systems"
]

# These fields should always have non-null content: you should know what page you are working with,
# where it comes from, and what notation is on it. In case of born-digital pages from data sources like
# **kernscores or Mutopia, the "institution_name" would ideally be the name of the institution responsible
# for the dataset, and if none applies, the name of the dataset can be used. The "shelfmark" field would
# be the ID of the composition in the dataset as assigned *by* that dataset (whatever you would use to find
# the given item within the dataset). The page number is just the page number according to whatever
# rendering mechanism you used for that item from the dataset.
# If the image itself cannot be linked directly (preferred), a link at least to the catalogue record
# or some other resource that enables verifying where the image comes from must be provided.
METADATA_REQUIRED_NONNULL_FIELDS = ["file_name",
                                    "institution_name", "shelfmark", "page_number",
                                    "link",
                                    "notation", "production", "notation_complexity", "clarity", "systems"]

# Some of the metadata fields related to notation type and quality have controlled vocabularies.
METADATA_CONTROLLED_VOCABULARIES = {
    "notation": {"CWMN", "mensural", "square", "adiastematic", "instrument-specific", "other"},
    "notation_complexity": {'monophonic', 'homophonic', 'polyphonic', 'pianoform'},
    "production": {"printed", "handwritten", "born-digital"},
    "clarity": {'perfect', 'sufficient', 'problematic', 'unreadable'},
    "systems": {'single-staff', 'grand-staff', 'multi-instrument', 'variable'}
}


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


def normalised_metadata_entry(csv_dict):
    '''Filters the loaded metadata to only include the fields defined in METADATA_DEFINED_FIELDS.
    This is useful to remove any extra fields that might be present in the CSV, and to ensure that
    the output JSON entries have a consistent format.'''
    normalised_dict = {field: csv_dict.get(field, None)
                       for field in METADATA_DEFINED_FIELDS}

    processed_page_size = process_page_size(normalised_dict["page_size"])
    normalised_dict["page_size"] = processed_page_size

    # Here may be other steps.

    return normalised_dict


def validate_metadata_entry(csv_dict,
                          check_rism: bool = False,
                          ) -> bool:
    '''Verifies that the loaded metadata conforms to the specification for MusiCorpus.
    Expected content example:

    {
      "file_name": "images/some-file-name.jpg",
      "institution_name": "Moravian State Library",
      "institution_rism_siglum": "CZ-Bu",
      "instituion_local_siglum": "MZK",
      "shelfmark": null,
      "rism_id_number": "sources/1001086460",
      "date": 1804
      "page_number": 14,
      "page_size": [235, 285],
      "scribal_data": null,
      "link": "https://www.e-rara.ch/mab/content/zoom/28920816",
      "title_description": "Sonata I [G-Dur op. 40 Nr. 1]",
      "author": "Muzio Clementi",
      "author_date": "1752-1832",
      "genre_form": "piano sonata",
      "notation": "CWMN",
      "notation_detailed": null,
      "production": "printed",
      "production_detailed": "19th century engraving, highly standardised",
      "notation_complexity": "pianoform",
      "clarity": "perfect",
      "systems": "grand_staffs"
    }
    '''

    # Run all checks, don't fail immediately, so we can report all issues with the entry at once.
    is_valid = True

    # Check that all fields are present.
    for field in METADATA_DEFINED_FIELDS:
        if field not in csv_dict:
            logging.warning(f"Metadata entry is missing required field '{field}'")
            is_valid = False

    # Check that fields with controlled vocabularies have valid values.
    for field, allowed_values in METADATA_CONTROLLED_VOCABULARIES.items():
        if csv_dict[field] not in allowed_values:
            logging.warning(f"Metadata entry '{csv_dict['file_name']}' has invalid value '{csv_dict[field]}' for field '{field}'")
            is_valid = False

    return is_valid


def build_page_name_to_metadata_dict(metadata_entries: list, page_names: list[str]) -> dict:
    """Builds a dictionary mapping page names (defined as basenames of the file_name field)
    to their metadata entries."""
    all_metadata_dict = {os.path.splitext(os.path.basename(entry['file_name']))[0]: entry
                         for entry in metadata_entries}
    metadata_dict = {page_name: all_metadata_dict[page_name] for page_name in page_names}
    return metadata_dict


def prepare_metadata_per_page(metadata: list[dict[str, str]], page_names: list[str]):
    """Prepares metadata from what was loaded from the CSV export of our metadata google sheet
    into the form that can then be exported for each page.

    Returns a dictionary with page_names as keys and the normalised metadata entry as values.
    """
    # Select metadata entries for the pages in our dataset
    selected_metadata = []
    for page_name in page_names:
        # We use startswith(page_name) because the file_name entry has the format extension.
        # Note that the file_name field will need to be modified to the proper path,
        # for now we use it as the source of the UUID string that we use to identify pages.
        available_entries = [entry for entry in metadata if entry['file_name'].startswith(page_name)]
        if len(available_entries) < 1:
            logging.warning(f"No metadata entry found for page {page_name}")
        if len(available_entries) > 1:
            logging.warning(f"Multiple metadata entries found for page {page_name}. Selecting the first one.")
        else:
            selected_metadata.append(available_entries[0])

    normalised_metadata = [normalised_metadata_entry(entry) for entry in selected_metadata]
    valid_metadata = [entry for entry in normalised_metadata if validate_metadata_entry(entry)]

    if len(valid_metadata) < len(normalised_metadata):
        # Collect all invalid entries for reporting.
        invalid_entries = [entry for entry in normalised_metadata if not validate_metadata_entry(entry)]
        logging.warning(f"{len(invalid_entries)} metadata entries are invalid! Here are the invalid entries:\n{invalid_entries}")

        raise ValueError(f"{len(normalised_metadata) - len(valid_metadata)} metadata entries are invalid!"
                         f" TODO:write more useful error message.")

    metadata_dict = build_page_name_to_metadata_dict(valid_metadata, page_names)
    return metadata_dict


def output_metadata_entries_per_page(metadata_entries: list, page_names: list, dataset_root_dir: Path):
    """Outputs the individual metadata entries for each page in the expected JSON format.
    The output file will be `[dataset_root_dir]/[page_name]/metadata.json` for each page.
    """
    _metadata_entries_dict = {os.path.splitext(os.path.basename(entry['file_name']))[0]: entry
                              for entry in metadata_entries}
    for page_name in page_names:
        # Check that metadata for the page name exist.
        if page_name not in _metadata_entries_dict:
            raise ValueError(f"No metadata entry found for page {page_name}!")
        entry = _metadata_entries_dict[page_name]

        output_dir = dataset_root_dir / page_name
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        output_file = output_dir / "metadata.json"
        with open(output_file, "w") as f:
            json.dump(entry, f, indent=2)


def check_all_pages_have_metadata_exported(page_names: list, dataset_root_dir: Path):
    """Checks that all pages have their metadata exported to the expected location."""
    missing_metadata_pages = []
    for page_name in page_names:
        metadata_file = dataset_root_dir / page_name / "metadata.json"
        if not os.path.isfile(metadata_file):
            missing_metadata_pages.append(page_name)
    all_pages_have_metadata = len(missing_metadata_pages) == 0

    if not all_pages_have_metadata:
        logging.warning(f"The following {len(missing_metadata_pages)} pages are missing metadata exports:\n{missing_metadata_pages}")
    else:
        logging.info(f"All {len(page_names)} pages have their metadata exported.")

    return all_pages_have_metadata


##########################################################################################
# The following functions deal with creating approximately optimally stratified splits.


def split_metadata_statistics(metadata, uuids):
    """Report summary statistics on notation categories for a proposed list of UUIDs."""
    # Making this compatible with outputs of prepare_metadata_per_page.
    if isinstance(metadata, dict):
        metadata = list(metadata.values())

    selected_metadata = [entry for entry in metadata
                         if entry['file_name'].startswith(tuple(uuids))]
    summary_statistics = {
        category: {value: 0 for value in allowed_values}
        for category, allowed_values in METADATA_CONTROLLED_VOCABULARIES.items()
    }
    for entry in selected_metadata:
        for category in METADATA_CONTROLLED_VOCABULARIES.keys():
            value = entry.get(category, None)
            if value in summary_statistics[category]:
                summary_statistics[category][value] += 1

    # Compute proportional statistics
    proportional_statistics = {
        category: {value: count / len(selected_metadata) if len(selected_metadata) > 0 else 0
                   for value, count in value_counts.items()}
        for category, value_counts in summary_statistics.items()
    }
    return summary_statistics, proportional_statistics


def evaluate_split_stratification(metadata, train_uuids: list, val_uuids: list, test_uuids: list):
    """Measures how balanced are proportions of different metadata.

    So far this is just done by computing the total elementwise distance
    between the proportions of different metadata categories in the train, val, and test splits.

    The considered metadata categories are those with controlled vocabularies:
    `notation`, `notation_complexity`, `production`, `clarity`, `systems`.
    These categories are relevant to OMR system performance.
    """
    train_statistics, train_proportions = split_metadata_statistics(metadata, train_uuids)
    val_statistics, val_proportions = split_metadata_statistics(metadata, val_uuids)
    test_statistics, test_proportions = split_metadata_statistics(metadata, test_uuids)

    def _dist_element(x, y):
        # Euclidean.
        return np.sqrt((y - x)**2)

    # Measure total elementwise distance
    total_distance = 0
    for category in METADATA_CONTROLLED_VOCABULARIES.keys():
        for value in METADATA_CONTROLLED_VOCABULARIES[category]:
            train_prop = train_proportions[category][value]
            val_prop = val_proportions[category][value]
            test_prop = test_proportions[category][value]
            total_distance += _dist_element(train_prop, val_prop)
            total_distance += _dist_element(train_prop, test_prop)
            total_distance += _dist_element(val_prop, test_prop)

    return total_distance


def random_split(uuids: list, train_proportion: float=0.6, validation_proportion: float=0.2):
    """Randomly splits a list of UUIDs into train, validation,
    and test splits according to the specified proportions."""
    uuids = list(uuids)
    np.random.shuffle(uuids)
    n = len(uuids)
    train_end = int(n * train_proportion)
    val_end = int(n * (train_proportion + validation_proportion))
    train_uuids = uuids[:train_end]
    val_uuids = uuids[train_end:val_end]
    test_uuids = uuids[val_end:]
    return train_uuids, val_uuids, test_uuids


def random_split_no_book_overlap(uuids: list, train_proportion: float=0.6, validation_proportion: float=0.2) -> tuple:
    """Randomly splits a list of UUIDs into train, validation, and test splits
    according to the specified proportions, but makes sure to always include all samples
    from a single book in just one of the three subsets. The book is encoded by the first
    part of the UUID, which has the form `book-uuid_page-uuid`."""
    books = {}
    for uuid in uuids:
        book_uuid = uuid.split("_")[0]
        if book_uuid not in books:
            books[book_uuid] = []
        books[book_uuid].append(uuid)
    counts_per_book = {book_uuid: len(book_uuids) for book_uuid, book_uuids in books.items()}
    book_uuids = list(books.keys())
    np.random.shuffle(book_uuids)
    n_books = len(book_uuids)
    n_uuids = len(uuids)

    train_uuids = []
    val_uuids = []
    test_uuids = []
    train_count = 0
    val_count = 0
    test_count = 0

    # Now we have to take into account the number of uuids per book.
    for book_uuid in book_uuids:
        book_uuids = books[book_uuid]
        book_count = counts_per_book[book_uuid]
        if train_count + book_count <= n_uuids * train_proportion:
            train_uuids.extend(book_uuids)
            train_count += book_count
        elif val_count + book_count <= n_uuids * validation_proportion:
            val_uuids.extend(book_uuids)
            val_count += book_count
        else:
            test_uuids.extend(book_uuids)
            test_count += book_count

    return train_uuids, val_uuids, test_uuids


def find_best_random_split(metadata, uuids, allow_book_overlap=True,
                           n_splits=1000, train_proportion=0.6, validation_proportion=0.2):
    """Generate `n_splits` random splits, evaluate their stratification, and return
    the best one.

    Returns a tuple of UUID lists `(train, val, test)`,
    and the stratification distance of the best split."""
    best_split = None
    best_distance = float('inf')
    for i in range(n_splits):
        if allow_book_overlap:
            train_uuids, val_uuids, test_uuids = random_split(uuids,
                                                              train_proportion=train_proportion,
                                                              validation_proportion=validation_proportion)
        else:
            train_uuids, val_uuids, test_uuids = random_split_no_book_overlap(
                uuids,
                train_proportion=train_proportion,
                validation_proportion=validation_proportion)
        distance = evaluate_split_stratification(metadata,
                                                 train_uuids, val_uuids, test_uuids)
        if distance < best_distance:
            best_distance = distance
            best_split = (train_uuids, val_uuids, test_uuids)

    return best_split, best_distance


def report_stratification_of_split(split, normalised_metadata):
    """Report how a given split stratifies the metadata.
    Prints counts across triplets of train-val-test counts."""
    # Print stats for the individual splits.
    train_uuids, val_uuids, test_uuids = split
    train_stats, _ = split_metadata_statistics(normalised_metadata, train_uuids)
    val_stats, _ = split_metadata_statistics(normalised_metadata, val_uuids)
    test_stats, _ = split_metadata_statistics(normalised_metadata, test_uuids)
    # Merge the statistics so that each value is a triplet [train_count, val_count, test_count]
    merged_stats = {}
    for category in METADATA_CONTROLLED_VOCABULARIES.keys():
        merged_stats[category] = {}
        for value in METADATA_CONTROLLED_VOCABULARIES[category]:
            merged_stats[category][value] = [train_stats[category][value],
                                             val_stats[category][value],
                                             test_stats[category][value]]
    pprint.pprint(merged_stats)


def output_split_to_json(split: tuple, json_file: Path):
    train_uuids, val_uuids, test_uuids = split
    split_dict = {"train": train_uuids, "validation": val_uuids, "test": test_uuids}
    with open(json_file, "w") as f:
        json.dump(split_dict, f, indent=2)


###################################################################################################################
# Running this as a script: verify metadata.

def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-m', '--metadata_csv', type=Path, required=True,
                        help='Path to the input CSV file with metadata.')
    parser.add_argument("-p", "--page_names_file", type=Path, required=True,
                        help="Path to the file with page names " +
                             "(book-uuid_page-uuid), one per line." +
                             "Can include line-comments with hash # symbol")

    parser.add_argument('--n_random_splits', type=int, default=100000,
                        help='How many random splits to try when brute-forcing'
                             ' optimal stratification into train-val-test splits.')

    parser.add_argument('--permissive_split_json', type=Path,
                        help='Output the permissive split to this JSON file.'
                             ' The structure is a top-level dict with train, validation,'
                             ' and test keys, and each of them contains a list of page names.')
    parser.add_argument('--strict_split_json', type=Path,
                        help='Output the strict split (no book overlap) to this JSON file.'
                             ' The structure is a top-level dict with train, validation,'
                             ' and test keys, and each of them contains a list of page names.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()

    # read page names
    with open(args.page_names_file) as f:
        page_names = [
            l.strip() for l in f.readlines()
            if l.strip() != "" and not l.startswith("#")
        ]
        assert len(set(page_names)) == len(page_names), "Page names contain duplicates"

    # Load the metadata CSV
    with open(args.metadata_csv) as f:
        reader = csv.DictReader(f)
        metadata = list(reader)

    # Print sample
    logging.info(f"Loaded {len(metadata)} metadata entries from {args.metadata_csv}. Sample entry:")
    if len(metadata) > 0:
        logging.debug('\n'.join(map(str, metadata[:10])))
    else:
        logging.warning(f"No metadata entries found in {args.metadata_csv}.")

    # Wrapping up loading and normalisation
    normalised_metadata = prepare_metadata_per_page(metadata, page_names)

    #############################################################################
    # Finding optimally stratified splits

    # Try to find the best-stratified split
    best_split, best_stratification = find_best_random_split(normalised_metadata,
                                                             page_names,
                                                             n_splits=args.n_random_splits)
    print('Best split of {} tried: stratification value {}'.format(args.n_random_splits, best_stratification))
    report_stratification_of_split(best_split, normalised_metadata)
    # Save split if asked to do so
    if args.permissive_split_json is not None:
        output_split_to_json(best_split, args.permissive_split_json)

    # Now find the best-stratified split with no overlap in books between subsets.
    best_strict_split, best_strict_stratification = find_best_random_split(normalised_metadata,
                                                                           page_names,
                                                                           allow_book_overlap=False,
                                                                           n_splits=args.n_random_splits)
    print('Best STRICT split of {} tried: stratification value {}'.format(args.n_random_splits, best_strict_stratification))
    report_stratification_of_split(best_strict_split, normalised_metadata)
    # Save strict split if asked to do so
    if args.strict_split_json is not None:
        strict_split_json = args.strict_split_json
        output_split_to_json(best_strict_split, strict_split_json)

    _end_time = time.process_time()
    logging.info('scrape_cantus_db_sources.py done in {0:.3f} s'.format(_end_time - _start_time))



if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
