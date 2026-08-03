import argparse
import shutil
import sys
from pathlib import Path

from .extras import requires

NAME = "olimpic"

DESCRIPTION = "Export the UFAL OLiMPiC dataset into the MusiCorpus format"

DEFAULT_JPEG_QUALITY = 20
"""How hard the exported `image.jpg` files are compressed, unless told otherwise.

Low, and deliberately so. MusiCorpus requires the image to be available as
JPEG, but OLiMPiC ships PNG, and these images are the worst case for JPEG and
the best case for PNG: grayscale, near-bilevel, mostly white paper. Written at
OpenCV's default quality of 95, the export comes out about seven times the
size of the archive it was built from.

At quality 20 the synthetic variant lands at roughly the size of its source
PNGs and the scanned variant at about twice, which is as close to parity as
JPEG gets on scanned paper. The cost is visible ringing around staff lines and
note heads at 1:1 zoom, while every symbol stays unambiguous — for data that
exists to train recognition models, that reads as a mild augmentation rather
than as damage. Raise it with `--jpeg-quality` when a use case needs the
pixels, or keep the originals losslessly with `--png`.

It lives here rather than beside `ImageOutput` because `define_parser` has to
state the default in `--help`, and this module must not import OpenCV to do
it — `tests/test_cli.py` fails the build if it does.
"""

OUTPUT_FOLDER_NAMES = {
    "scanned": "UFAL.OlimpicScanned",
    "synthetic": "UFAL.OlimpicSynthetic",
}
"""What the output folder must be called for each variant.

OLiMPiC is distributed as two datasets that differ in their images, so they
become two MusiCorpus datasets rather than one. The name is checked rather
than imposed, so that a mistyped `--variant` is caught before an export runs
for twenty minutes and writes the wrong manifest.
"""


def define_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--olimpic",
        type=Path,
        required=True,
        help="Path to the untarred input folder, e.g. 'olimpic-1.0-scanned', "
        + "downloaded from https://github.com/ufal/olimpic-icdar24/releases/tag/datasets",
    )
    parser.add_argument(
        "--variant",
        choices=sorted(OUTPUT_FOLDER_NAMES.keys()),
        required=True,
        help="Which of the two distributed OLiMPiC datasets the input folder is",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output folder, named 'UFAL.OlimpicScanned' "
        + "or 'UFAL.OlimpicSynthetic' to match --variant",
    )
    parser.add_argument(
        "--force", action="store_true", help="Forces an overwrite of the output folder"
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=DEFAULT_JPEG_QUALITY,
        metavar="1-100",
        help=f"Quality of the exported image.jpg files (default: {DEFAULT_JPEG_QUALITY}). "
        + "The default is low on purpose, so that the export stays near the size of "
        + "the archive it was built from; raise it if you need the pixels",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also writes a lossless image.png beside each image.jpg. "
        + "MusiCorpus requires the JPEG and permits the PNG alongside it, so this "
        + "keeps the original quality available at the price of a larger dataset",
    )
    parser.add_argument(
        "--skip-specification-pdf",
        action="store_true",
        help="Skips downloading musicorpus-specification.pdf into the dataset, "
        + "for exporting without a network connection",
    )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace):
    with requires("exporters"):
        from ..exporters.olimpic.export_olimpic import export_olimpic
        from ..exporters.olimpic.write_image import ImageOutput

    input_folder = Path(args.olimpic)
    variant = str(args.variant)
    output_folder = Path(args.output)
    force = bool(args.force)
    jpeg_quality = int(args.jpeg_quality)
    write_png = bool(args.png)
    skip_specification_pdf = bool(args.skip_specification_pdf)

    # check the input folder
    if not input_folder.is_dir():
        print(f"The input folder does not exist: {input_folder}")
        sys.exit(1)

    # check the JPEG quality
    if not 1 <= jpeg_quality <= 100:
        print(f"The --jpeg-quality must be between 1 and 100, got {jpeg_quality}.")
        sys.exit(1)

    # check output folder name
    expected_name = OUTPUT_FOLDER_NAMES[variant]
    if output_folder.name != expected_name:
        print(f"The output folder must be called '{expected_name}' for --variant {variant}.")
        sys.exit(1)

    # clear the output folder
    if output_folder.exists() and not force:
        print("The output folder already exists. Use --force to overwrite it.")
        sys.exit(1)
    if output_folder.exists() and force:
        shutil.rmtree(output_folder)

    # run the extraction process
    export_olimpic(
        input_folder=input_folder,
        variant=variant,  # type: ignore[arg-type]  # argparse `choices` guarantees the literal
        output_folder=output_folder,
        image_output=ImageOutput(jpeg_quality=jpeg_quality, write_png=write_png),
        skip_specification_pdf=skip_specification_pdf,
    )
