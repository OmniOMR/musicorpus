"""Builds a MusiCorpus dataset out of one distributed OLiMPiC variant.

OLiMPiC has no page images and no page-level annotation — it is grandstaff
crops and grandstaff transcriptions, cut out of scores whose pages are not
part of the distribution. So the export produces page folders that hold no
files of their own, only `Grandstaves/` and `Staves/` subdivisions. The
specification describes exactly this shape in its Example 3.
"""

import shutil
from datetime import datetime
from pathlib import Path

from ...error_bag import ErrorBag
from ...manifest import MusicorpusManifest
from ...splits import Splits
from ..download_specification_pdf import download_specification_pdf
from .export_samples import export_samples
from .input_olimpic_folder import InputOlimpicFolder, OlimpicVariant
from .write_image import ImageOutput


def export_olimpic(
    input_folder: Path,
    variant: OlimpicVariant,
    output_folder: Path,
    image_output: ImageOutput,
    skip_specification_pdf: bool = False,
):
    """Run the dataset export process (converts OLiMPiC into MusiCorpus)"""

    errors = ErrorBag()
    now = datetime.now()
    assets_folder = Path(__file__).parent / "assets"

    olimpic = InputOlimpicFolder(folder=input_folder, variant=variant)

    # === root ===

    output_folder.mkdir(parents=True)

    # musicorpus-specification.pdf
    if not skip_specification_pdf:
        download_specification_pdf(output_folder / "musicorpus-specification.pdf")

    # musicorpus.json
    manifest = MusicorpusManifest.load_from_file(assets_folder / f"musicorpus.{variant}.json")
    manifest.created_at = now
    manifest.write_to_file(output_folder / "musicorpus.json")

    # README.md
    shutil.copy(assets_folder / f"README.{variant}.md", output_folder / "README.md")

    # LICENSE.txt
    # taken from the input rather than kept as an asset of this repository,
    # so that the exported dataset carries the licence OLiMPiC shipped with
    shutil.copy(olimpic.license_path, output_folder / "LICENSE.txt")

    # splits.json
    page_names_by_split = olimpic.page_names_by_split()
    splits = Splits(
        # `[]` rather than a missing key for a split the variant does not have.
        # The scanned variant ships no training data, and the specification
        # asks splits.json to keep its train-validation-test shape.
        train=page_names_by_split.get("train", []),
        validation=page_names_by_split.get("validation", []),
        test=page_names_by_split.get("test", []),
    )
    splits.write_to_file(output_folder / "splits.json")

    # === pages ===

    summary = export_samples(
        input_folder=olimpic,
        output_folder=output_folder,
        image_output=image_output,
        errors=errors,
    )

    # === finalize ===

    # a page whose every sample failed would be listed in splits.json without
    # existing on disk, which `musicorpus validate` would report far from here
    exported_page_names = [f.name for f in output_folder.iterdir() if f.is_dir()]
    if not splits.check_that_it_covers_page_names_exactly(
        exported_page_names, raise_on_failure=False
    ):
        errors.add_error(
            "root",
            "splits.json does not cover the exported page folders exactly. "
            + "Some pages listed in the splits failed to export.",
        )

    print()
    print(f"Images written as JPEG at quality {image_output.jpeg_quality}", end="")
    print(", with a lossless PNG beside each" if image_output.write_png else "")
    print(f"Pages exported: {len(exported_page_names)}")
    print(f"Grandstaves exported: {summary.grandstaves}")
    print(f"Of those, separated into two staves: {summary.staff_pairs}")
    print(f"Of those, left whole (music crosses the staves): {summary.pianoform_grandstaves}")
    print(f"Of those, left whole (could not be separated): {summary.unseparable_grandstaves}")
    for reason, count in summary.unseparable_reasons.most_common():
        print(f"    {count}x {reason}")

    errors.write_report_if_any_errors(file_path=output_folder / "ERRORS.txt")
