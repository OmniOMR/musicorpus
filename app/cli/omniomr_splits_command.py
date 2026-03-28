import argparse
from pathlib import Path
from ..read_page_names import read_page_names
from ..omniomr.load_page_metadatas import load_page_metadatas
from ..Splits import Splits


def define_parser(parser: argparse.ArgumentParser):
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
        "--extend_splits",
        type=Path,
        required=False,
        default=None,
        help="Path to and existing splits.json file " +
            "that should be extended instead of generating " +
            "new splits from scratch"
    )
    parser.add_argument(
        "--n_attempts",
        type=int,
        required=True,
        help="How many iterations to run when finding splits, " +
            "in production run one million (1_000_000)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output 'splits.json' file"
    )
    parser.add_argument(
        "--book_consistent",
        action="store_true",
        help="Enforces book consistency - all pages of one " +
            "book will land in one split only"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forces an overwrite of the output folder"
    )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace):
    metadata_file_path = Path(args.metadata)
    page_names_file_path = Path(args.page_names)
    extend_splits_path = None if args.extend_splits is None \
        else Path(args.extend_splits)
    n_attempts = int(args.n_attempts)
    book_consistent = bool(args.book_consistent)
    output_file = Path(args.output)
    force = bool(args.force)

    # read page names
    page_names = read_page_names(page_names_file_path)

    # load the existing splits file before clearing the output
    # file in the case that it is the same file
    existing_splits = Splits.make_empty()
    if extend_splits_path is not None:
        existing_splits = Splits.read_from_file(
            extend_splits_path,
            run_assertions=True
        )
        if book_consistent:
            # TODO: check that the loaded splits are book consistent
            raise NotImplementedError()

    # clear the output file
    if output_file.exists() and not force:
        print("The output file already exists. Use --force to overwrite it.")
        exit()
    if output_file.exists() and force:
        output_file.unlink()

    # read metadata
    page_metadatas = load_page_metadatas(
        metadata_file_path=metadata_file_path,
        dpi_file=None
    )

    # run the splits defining process
    # TODO
    print("Hello world!")
