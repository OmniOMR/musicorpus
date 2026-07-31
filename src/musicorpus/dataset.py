"""Reading a MusiCorpus dataset from disk.

This is the entry point for consuming a dataset:

    from musicorpus import Dataset

    dataset = Dataset.load(Path("datasets/UFAL.OmniOMR"))
    for page in dataset.split("train"):
        for sample in page.staves:
            musicxml = sample.transcription_path("musicxml")

The formats MusiCorpus itself defines — the manifest, the splits, the layout,
the page metadata, the image subdivisions — are parsed and handed back as
objects. Everything else is handed back as a `Path`: MusicXML, MuNG, kern, MEI
and the images belong to other libraries, and reading them needs dependencies
this package deliberately does not have. Use your own loader on the path.

Nothing here touches the disk until asked. Constructing a `Dataset` reads the
manifest and nothing else; pages, subdivisions and files are looked up when
they are first used, so opening a dataset of ten thousand pages is cheap.
"""

import json
from collections.abc import Iterator
from functools import cached_property
from pathlib import Path

from .image_subdivisions import ImageSubdivisions
from .layout import Layout
from .manifest import MusicorpusManifest
from .page_metadata import PageMetadata
from .splits import Splits

MANIFEST_FILE_NAME = "musicorpus.json"
"""The file whose presence makes a folder a MusiCorpus dataset."""

SUBDIVISION_KINDS = ("Staves", "Grandstaves", "Systems")
"""The subdivision folders a page may contain, named as on disk."""

TRANSCRIPTION_FORMATS = ("musicxml", "krn", "mei", "ly", "midi", "mung", "mscz", "dorico", "sib")
"""Transcription suffixes the specification names, most useful first."""

IMAGE_SUFFIXES = ("jpg", "png", "tif")
"""Image suffixes the specification allows, in the order it recommends."""


class NotAMusicorpusDataset(Exception):
    """Raised when a folder is opened as a dataset but has no manifest."""


class Sample:
    """A folder holding an image and transcriptions of what is on it.

    Both a page and a subdivision of a page are samples, and they carry the
    same repertoire of files, so anything reading images and transcriptions
    can take either.
    """

    def __init__(self, path: Path, dataset: "Dataset", page_name: str) -> None:
        self.path = path
        """Path to this sample's folder."""

        self.dataset = dataset
        """The dataset this sample belongs to."""

        self.page_name = page_name
        """Name of the page this sample belongs to (its own name, for a page)."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self.path)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sample):
            return NotImplemented
        return type(self) is type(other) and self.path == other.path

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.path))

    # === images ===

    def image_path(self, variant: str | None = None, suffix: str | None = None) -> Path | None:
        """Path to this sample's image, or None if it has none.

        `variant` picks one of the `image.{variant}.jpg` alternatives; the
        default is the plain `image.jpg`. With no `suffix`, the recommended
        suffixes are tried in order, so a born-digital dataset shipping only
        `image.png` is found without the caller having to ask for it.
        """
        stem = "image" if variant is None else f"image.{variant}"
        suffixes = (suffix,) if suffix is not None else IMAGE_SUFFIXES
        for candidate in suffixes:
            path = self.path / f"{stem}.{candidate}"
            if path.exists():
                return path
        return None

    def image_variants(self) -> list[str]:
        """Names of the `image.{variant}` alternatives present, sorted.

        The default `image.jpg` is not a variant and is not listed; ask for it
        with `image_path()`.
        """
        variants: set[str] = set()
        for suffix in IMAGE_SUFFIXES:
            for path in self.path.glob(f"image.*.{suffix}"):
                variants.add(path.name[len("image.") : -len(f".{suffix}")])
        return sorted(variants)

    # === transcriptions ===

    def transcription_path(self, format: str) -> Path | None:
        """Path to `transcription.{format}`, or None if this sample has none."""
        path = self.path / f"transcription.{format}"
        return path if path.exists() else None

    def transcription_formats(self) -> list[str]:
        """Which of the specified transcription formats this sample has."""
        return [
            format
            for format in TRANSCRIPTION_FORMATS
            if (self.path / f"transcription.{format}").exists()
        ]

    # === the JSON formats MusiCorpus defines ===

    @property
    def metadata_path(self) -> Path | None:
        path = self.path / "metadata.json"
        return path if path.exists() else None

    def metadata(self) -> PageMetadata | None:
        """The parsed `metadata.json`, or None if this sample has none."""
        path = self.metadata_path
        return None if path is None else PageMetadata.load_from_file(path)

    @property
    def coco_path(self) -> Path | None:
        path = self.path / "coco-object-detection.json"
        return path if path.exists() else None

    @property
    def mung_to_coco_map_path(self) -> Path | None:
        path = self.path / "mung-to-coco-ids-map.json"
        return path if path.exists() else None


class Subdivision(Sample):
    """One staff, grandstaff or system of a page."""

    def __init__(self, path: Path, page: "Page", kind: str) -> None:
        super().__init__(path=path, dataset=page.dataset, page_name=page.name)

        self.page = page
        """The page this subdivision was cut from."""

        self.kind = kind
        """Which subdivision folder this came from: one of `SUBDIVISION_KINDS`."""

    @property
    def name(self) -> str:
        """The subdivision's folder name, e.g. `2`, `6-7` or `2-7`."""
        return self.path.name


class Page(Sample):
    """One page of a dataset: one folder directly inside the dataset folder."""

    def __init__(self, path: Path, dataset: "Dataset") -> None:
        super().__init__(path=path, dataset=dataset, page_name=path.name)

    @property
    def name(self) -> str:
        """The page's folder name, which is how splits refer to it."""
        return self.path.name

    def exists(self) -> bool:
        """Whether this page's folder is actually present.

        A splits file may name a page that is not in the dataset, so a page
        obtained from a split is not guaranteed to be on disk.
        """
        return self.path.is_dir()

    # === subdivisions ===

    def subdivisions(self, kind: str) -> list[Subdivision]:
        """The subdivisions of one kind, sorted by folder name.

        Sorting is lexicographic rather than numeric, because subdivision
        names are specified as arbitrary path-safe strings — `10` sorts before
        `2`. Sort by something else if your dataset numbers them.
        """
        folder = self.path / kind
        if not folder.is_dir():
            return []
        return [
            Subdivision(path=path, page=self, kind=kind)
            for path in sorted(folder.iterdir(), key=lambda p: p.name)
            if path.is_dir()
        ]

    @property
    def staves(self) -> list[Subdivision]:
        return self.subdivisions("Staves")

    @property
    def grandstaves(self) -> list[Subdivision]:
        return self.subdivisions("Grandstaves")

    @property
    def systems(self) -> list[Subdivision]:
        return self.subdivisions("Systems")

    # === page-only files ===

    def layout(self) -> Layout | None:
        """The parsed `layout.json`, or None if this page has none."""
        path = self.path / "layout.json"
        return None if not path.exists() else Layout.load_from_file(path)

    def image_subdivisions(self, variant: str | None = None) -> ImageSubdivisions | None:
        """The parsed `subdivisions.image.json`, or None if this page has none.

        `variant` picks the mapping for an image variant, from
        `subdivisions.image.{variant}.json`.
        """
        name = (
            "subdivisions.image.json" if variant is None else f"subdivisions.image.{variant}.json"
        )
        path = self.path / name
        return None if not path.exists() else ImageSubdivisions.load_from(path)

    @property
    def subdivisions_coco_path(self) -> Path | None:
        path = self.path / "subdivisions.coco-object-detection.json"
        return path if path.exists() else None


class Dataset:
    """A MusiCorpus dataset: a folder with a `musicorpus.json` in it."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        """Path to the dataset folder, e.g. `datasets/UFAL.OmniOMR`."""

    def __repr__(self) -> str:
        return f"Dataset({str(self.path)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dataset):
            return NotImplemented
        return self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)

    @staticmethod
    def load(path: Path) -> "Dataset":
        """Opens a dataset folder, checking that it is one.

        Raises `NotAMusicorpusDataset` when the folder has no manifest, which
        is what distinguishes a MusiCorpus dataset from any other folder that
        happens to sit in the same root.
        """
        path = Path(path)
        if not (path / MANIFEST_FILE_NAME).exists():
            raise NotAMusicorpusDataset(
                f"There is no {MANIFEST_FILE_NAME} in {path}, so it is not a MusiCorpus dataset."
            )
        return Dataset(path)

    @staticmethod
    def is_dataset(path: Path) -> bool:
        """Whether the folder holds a manifest and so is a MusiCorpus dataset."""
        return (Path(path) / MANIFEST_FILE_NAME).exists()

    @staticmethod
    def find_all(root: Path) -> list["Dataset"]:
        """Every MusiCorpus dataset directly inside a root folder, sorted.

        A root may hold datasets that do not follow the format; those have no
        manifest and are skipped rather than reported.
        """
        root = Path(root)
        if not root.is_dir():
            return []
        return [
            Dataset(path)
            for path in sorted(root.iterdir(), key=lambda p: p.name)
            if path.is_dir() and Dataset.is_dataset(path)
        ]

    @property
    def name(self) -> str:
        """The dataset folder's name, e.g. `UFAL.OmniOMR`."""
        return self.path.name

    @cached_property
    def manifest(self) -> MusicorpusManifest:
        """The parsed `musicorpus.json`, read once and remembered."""
        return MusicorpusManifest.load_from_file(self.path / MANIFEST_FILE_NAME)

    # === pages ===

    @cached_property
    def page_names(self) -> list[str]:
        """Names of every page folder in the dataset, sorted.

        This is what is on disk, which is not necessarily what the splits
        cover — the specification allows a splits file to leave pages out.
        """
        return sorted(
            path.name
            for path in self.path.iterdir()
            if path.is_dir() and path.name not in SUBDIVISION_KINDS
        )

    def page(self, name: str) -> Page:
        """A page by name, whether or not its folder exists."""
        return Page(path=self.path / name, dataset=self)

    def pages(self) -> Iterator[Page]:
        """Every page folder in the dataset, sorted by name."""
        for name in self.page_names:
            yield Page(path=self.path / name, dataset=self)

    # === splits ===

    def splits_path(self, variant: str | None = None) -> Path:
        """Path to `splits.json`, or to the named alternative splits file."""
        name = "splits.json" if variant is None else f"splits.{variant}.json"
        return self.path / name

    def splits(self, variant: str | None = None) -> Splits:
        """The parsed splits file.

        Assertions are deliberately not run on load: a reader should be able
        to open a dataset whose splits overlap in order to find that out,
        rather than failing to open it at all. `musicorpus validate` is what
        reports that as a defect.
        """
        return Splits.read_from_file(self.splits_path(variant), run_assertions=False)

    def split_variants(self) -> list[str]:
        """Names of the alternative splits files present, sorted.

        The default `splits.json` is not a variant and is not listed.
        """
        return sorted(
            path.name[len("splits.") : -len(".json")]
            for path in self.path.glob("splits.*.json")
            if path.name != "splits.json"
        )

    def split(self, split_name: str, variant: str | None = None) -> Iterator[Page]:
        """The pages of one split, in the order the splits file lists them.

        That order is meaningful: the specification asks for it to be
        shuffled, so it can be trained on directly.
        """
        for page_name in self.splits(variant)[split_name]:
            yield self.page(page_name)

    # === dataset-level files ===

    @property
    def readme_path(self) -> Path | None:
        path = self.path / "README.md"
        return path if path.exists() else None

    @property
    def license_path(self) -> Path | None:
        path = self.path / "LICENSE.txt"
        return path if path.exists() else None

    @property
    def coco_path(self) -> Path | None:
        """The dataset-global `coco-object-detection.json`, if there is one."""
        path = self.path / "coco-object-detection.json"
        return path if path.exists() else None

    @property
    def specification_pdf_path(self) -> Path | None:
        path = self.path / "musicorpus-specification.pdf"
        return path if path.exists() else None

    def coco(self) -> dict | None:
        """The dataset-global COCO file, as plain JSON.

        Returned unparsed because COCO is not a MusiCorpus format and reading
        its masks needs pycocotools, which the base install does not have.
        """
        path = self.coco_path
        if path is None:
            return None
        with open(path) as f:
            return json.load(f)
