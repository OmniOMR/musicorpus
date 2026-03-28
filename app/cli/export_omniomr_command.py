import argparse
from pathlib import Path
import shutil
from ..read_page_names import read_page_names
from ..omniomr.export_omniomr import export_omniomr
from ..omniomr.InputLayoutFile import InputLayoutFile
from ..omniomr.InputDpiFile import InputDpiFile
from ..omniomr.load_page_metadatas import load_page_metadatas


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
        "--layout",
        type=Path,
        required=True,
        help="Path to the input page-layout data .csv file"
    )
    parser.add_argument(
        "--dpi",
        type=Path,
        required=True,
        help="Path to the input page-DPI data .csv file"
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
    mung_studio_folder = Path(args.ms_documents)
    editions_folder = Path(args.ms_editions)
    metadata_file_path = Path(args.metadata)
    layout_file_path = Path(args.layout)
    dpi_file_path = Path(args.dpi)
    page_names_file_path = Path(args.page_names)
    output_folder = Path(args.output)
    force = bool(args.force)

    # read page names
    page_names = read_page_names(page_names_file_path)

    # check output folder name
    if output_folder.name != "UFAL.OmniOMR":
        print("The output folder must be called 'UFAL.OmniOMR'.")
        exit()

    # clear the output folder
    if output_folder.exists() and not force:
        print("The output folder already exists. Use --force to overwrite it.")
        exit()
    if output_folder.exists() and force:
        shutil.rmtree(output_folder)

    # read DPIs
    dpi_file = InputDpiFile.load(dpi_file_path)

    # read metadata
    page_metadatas = load_page_metadatas(
        metadata_file_path=metadata_file_path,
        dpi_file=dpi_file
    )
    
    # read layout
    layout_file = InputLayoutFile.load(layout_file_path)

    # run the extraction process
    export_omniomr(
        page_names=page_names,
        mung_studio_folder=mung_studio_folder,
        editions_folder=editions_folder,
        page_metadatas=page_metadatas,
        layout_file=layout_file,
        dpi_file=dpi_file,
        output_folder=output_folder,
    )
