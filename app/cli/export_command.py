import argparse
from pathlib import Path
import shutil
import csv
from ..perform_dataset_export import perform_dataset_export


def define_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--ms_documents",
        type=Path,
        required=True,
        help="Path to the input folder width MuNG Studio documents"
    )
    parser.add_argument(
        "--ms_editions",
        type=Path,
        required=True,
        help="Path to the input folder with .mscz MuseScore files"
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="Path to the input metadata .csv file"
    )
    parser.add_argument(
        "--page_names",
        type=Path,
        required=True,
        help="Path to the file with page names " +
            "(book-uuid_page-uuid), one per line." +
            "Can include line-comments with hash # symbol"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output 'UFAL.OmniOMR' folder"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forces an overwrite of the output folder"
    )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace):
    mung_studio_documents = Path(args.ms_documents)
    muse_score_editions = Path(args.ms_editions)
    metadata_file = Path(args.metadata)
    page_names_file = Path(args.page_names)
    output_directory = Path(args.output)
    force = bool(args.force)

    # read page names
    with open(page_names_file) as f:
        page_names = [
            l.strip() for l in f.readlines()
            if l.strip() != "" and not l.startswith("#")
        ]
        assert len(set(page_names)) == len(page_names), "Page names contain duplicates"

    # check output folder name
    if output_directory.name != "UFAL.OmniOMR":
        print("The output folder must be called 'UFAL.OmniOMR'.")
        exit()

    # clear the output folder
    if output_directory.exists() and not force:
        print("The output folder already exists. Use --force to overwrite it.")
        exit()
    if output_directory.exists() and force:
        shutil.rmtree(output_directory)

    # read metadata
    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        metadata = list(reader)

    # run the extraction process
    perform_dataset_export(
        page_names=page_names,
        mung_studio_folder=mung_studio_documents,
        editions_folder=muse_score_editions,
        metadata=metadata,
        output_folder=output_directory,
    )
