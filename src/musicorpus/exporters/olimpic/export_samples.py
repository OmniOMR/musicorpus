"""Turns each OLiMPiC sample into a grandstaff, and a staff pair where it can."""

import traceback
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import tqdm
from lmx.musicxml.grandstaff.unzip_grandstaff import ContainsTruePianoformMusicException
from lmx.musicxml.io.write_musicxml_tree_to_file import write_musicxml_tree_to_file

from ...error_bag import ErrorBag
from .declare_explicit_layout import declare_explicit_layout
from .input_olimpic_folder import InputOlimpicFolder, InputSample
from .split_grandstaff_image import split_grandstaff_image
from .unzip_grandstaff_musicxml import NotASingleGrandstaff, unzip_grandstaff_musicxml
from .write_image import ImageOutput


@dataclass
class ExportSummary:
    """Counts of what the export produced, for the closing report."""

    grandstaves: int = 0
    """Grandstaff folders written, which is one per input sample."""

    staff_pairs: int = 0
    """Grandstaves that were also separated into two staff folders."""

    pianoform_grandstaves: int = 0
    """Grandstaves left without staves because the music crosses the staves.

    Not an error. Piano music routinely runs a voice across both staves of the
    grandstaff, and such a grandstaff simply has no staff-level ground truth
    to offer — the specification says as much in its `Grandstaves` section.
    """

    unseparable_grandstaves: int = 0
    """Grandstaves left without staves for any other reason.

    Also not an error, but a rarer and less principled one: `lmx` assumes the
    input was canonicalized by MuseScore, and refuses a measure that does not
    hold to that — a `<backup>` that rewinds to somewhere other than the start
    of the measure, most of them. Skipping such a grandstaff is what the whole
    dataset does with music it cannot separate; the reasons are counted below
    so that a new kind of failure cannot hide among the known ones.
    """

    unseparable_reasons: Counter[str] = field(default_factory=Counter)
    """How many grandstaves each distinct failure message accounted for."""


def export_samples(
    input_folder: InputOlimpicFolder,
    output_folder: Path,
    image_output: ImageOutput,
    errors: ErrorBag,
) -> ExportSummary:
    """Writes every sample into the output dataset, subdivision by subdivision."""
    summary = ExportSummary()

    for sample in tqdm.tqdm(input_folder.all_samples(), "Exporting samples"):
        _export_sample(
            sample=sample,
            output_folder=output_folder,
            image_output=image_output,
            errors=errors,
            summary=summary,
        )

    return summary


def _reason_of(exception: Exception) -> str:
    """The message of an exception, without the part that varies per sample.

    `lmx` appends a dict of measure indexes and durations to its assertions,
    so one failure mode reads as a different message every time it happens.
    Cutting the message off at that dict groups them back together.
    """
    message = str(exception).split(" {")[0].strip()
    if message == "":
        return type(exception).__name__
    return f"{type(exception).__name__}: {message}"


def _export_sample(
    sample: InputSample,
    output_folder: Path,
    image_output: ImageOutput,
    errors: ErrorBag,
    summary: ExportSummary,
) -> None:
    if not sample.musicxml_path.exists():
        errors.add_error(sample.page_name, f"MusicXML file not found: {sample.musicxml_path}")
        return
    if not sample.image_path.exists():
        errors.add_error(sample.page_name, f"Image file not found: {sample.image_path}")
        return

    # UNCHANGED rather than COLOR: OLiMPiC images are grayscale, and decoding
    # them into three identical channels would only make every encoding of
    # them bigger
    image = cv2.imread(str(sample.image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        errors.add_error(sample.page_name, f"Image file could not be read: {sample.image_path}")
        return
    if image.ndim == 3 and image.shape[2] == 4:
        # JPEG has nowhere to put an alpha channel
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    try:
        musicxml_root = ET.fromstring(sample.musicxml_path.read_text("utf-8"))
    except Exception:
        errors.add_error(
            sample.page_name,
            f"MusicXML file could not be parsed: {sample.musicxml_path}\n" + traceback.format_exc(),
        )
        return

    # the source transcription already is the grandstaff transcription and is
    # carried over as it stands, save for this one declaration that MusiCorpus
    # requires and OLiMPiC files do not make. Declaring it here rather than on
    # the way out means the two staves inherit it with the rest of the header.
    declare_explicit_layout(musicxml_root)

    # === the grandstaff ===

    grandstaff_folder = output_folder / sample.page_name / "Grandstaves" / sample.grandstaff_name
    grandstaff_folder.mkdir(parents=True, exist_ok=True)

    write_musicxml_tree_to_file(
        grandstaff_folder / "transcription.musicxml", ET.ElementTree(musicxml_root)
    )
    # the grandstaff image is the source image whole, so a `.png` asked for
    # here can be the source file itself rather than a re-encoding of it
    image_output.write(grandstaff_folder, image, png_source=sample.image_path)
    summary.grandstaves += 1

    # === the two staves it may separate into ===

    try:
        upper_musicxml, lower_musicxml = unzip_grandstaff_musicxml(musicxml_root)
    except ContainsTruePianoformMusicException:
        summary.pianoform_grandstaves += 1
        return
    except (NotASingleGrandstaff, AssertionError) as exception:
        # a grandstaff that cannot be separated is skipped rather than forced,
        # so this is a count and a reason rather than an error
        summary.unseparable_grandstaves += 1
        summary.unseparable_reasons[_reason_of(exception)] += 1
        return
    except Exception:
        errors.add_error(
            sample.page_name,
            f"Failed to separate the staves of grandstaff {sample.grandstaff_name}: "
            + traceback.format_exc(),
        )
        return

    upper_image, lower_image = split_grandstaff_image(image)

    for staff_suffix, staff_musicxml, staff_image in (
        ("a", upper_musicxml, upper_image),
        ("b", lower_musicxml, lower_image),
    ):
        staff_folder = (
            output_folder / sample.page_name / "Staves" / (sample.grandstaff_name + staff_suffix)
        )
        staff_folder.mkdir(parents=True, exist_ok=True)
        write_musicxml_tree_to_file(staff_folder / "transcription.musicxml", staff_musicxml)
        image_output.write(staff_folder, staff_image)

    summary.staff_pairs += 1
