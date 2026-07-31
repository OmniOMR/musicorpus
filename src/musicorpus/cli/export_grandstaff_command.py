import argparse
import shutil
import sys
from pathlib import Path

from ..exporters.grandstaff.export_grandstaff import export_grandstaff


def define_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--grandstaff",
        type=Path,
        required=True,
        help="Path to the input grandstaff.tgz file, can be downloaded " +
        "from https://grfia.dlsi.ua.es/sheet-music-transformer/"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output 'PRAIG.GrandStaff' folder"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forces an overwrite of the output folder"
    )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace):
    grandstaff_tgz_path = Path(args.grandstaff)
    output_folder = Path(args.output)
    force = bool(args.force)

    # check output folder name
    if output_folder.name != "PRAIG.GrandStaff":
        print("The output folder must be called 'PRAIG.GrandStaff'.")
        sys.exit(1)

    # clear the output folder
    if output_folder.exists() and not force:
        print("The output folder already exists. Use --force to overwrite it.")
        sys.exit(1)
    if output_folder.exists() and force:
        shutil.rmtree(output_folder)

    # run the extraction process
    export_grandstaff(
        grandstaff_tgz_path=grandstaff_tgz_path,
        output_folder=output_folder
    )
