"""Tools for building and consuming datasets in the MusiCorpus format.

MusiCorpus is a set of guidelines for how an Optical Music Recognition dataset
is laid out on disk. This package reads such a dataset:

    from pathlib import Path

    from musicorpus import Dataset

    dataset = Dataset.load(Path("datasets/UFAL.OmniOMR"))
    print(dataset.manifest.full_dataset_name)

    for page in dataset.split("train"):
        for staff in page.staves:
            musicxml = staff.transcription_path("musicxml")

The names re-exported here are the public API; everything below them is
internal arrangement that may move between versions. Importing this package
pulls in nothing but the standard library — see `docs/python-api.md`.
"""

from .coco import (
    CocoBbox,
    CocoDatasetMetadata,
    CocoImageMetadata,
    CocoLicense,
)
from .dataset import (
    IMAGE_SUFFIXES,
    SUBDIVISION_KINDS,
    TRANSCRIPTION_FORMATS,
    Dataset,
    NotAMusicorpusDataset,
    Page,
    Sample,
    Subdivision,
)
from .error_bag import ErrorBag
from .image_subdivisions import ImageSubdivisions
from .layout import Layout
from .manifest import MusicorpusManifest
from .page_metadata import PageMetadata
from .splits import Splits

SPECIFICATION_VERSION = "1.0"
"""The version of the MusiCorpus specification this package implements.

It is what a conformant dataset carries in `musicorpus.json` as
`musicorpus_version`, and it moves with the specification rather than with the
version of this package — see the table in CLAUDE.md.
"""

__all__ = [
    "IMAGE_SUFFIXES",
    "SPECIFICATION_VERSION",
    "SUBDIVISION_KINDS",
    "TRANSCRIPTION_FORMATS",
    "CocoBbox",
    "CocoDatasetMetadata",
    "CocoImageMetadata",
    "CocoLicense",
    "Dataset",
    "ErrorBag",
    "ImageSubdivisions",
    "Layout",
    "MusicorpusManifest",
    "NotAMusicorpusDataset",
    "Page",
    "PageMetadata",
    "Sample",
    "Splits",
    "Subdivision",
]
