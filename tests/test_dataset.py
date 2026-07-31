"""Tests for the dataset reader, against the committed `TEST.Fixture` dataset.

The fixture is described in `tests/data/TEST.Fixture/README.md` and built by
`tests/data/build_test_fixture.py`. It holds the awkward cases on purpose: a
page with nothing but an image and a transcription, a page no split mentions, a
split naming a page that is not on disk, an image variant, a PNG-only page and
an alternative splits file.
"""

from pathlib import Path

import pytest

from musicorpus import (
    Dataset,
    ImageSubdivisions,
    Layout,
    NotAMusicorpusDataset,
    Page,
    PageMetadata,
    Subdivision,
)

DATA = Path(__file__).parent / "data"
FIXTURE = DATA / "TEST.Fixture"


@pytest.fixture
def dataset() -> Dataset:
    return Dataset.load(FIXTURE)


# === opening a dataset ===


def test_load_reads_the_manifest(dataset: Dataset) -> None:
    assert dataset.name == "TEST.Fixture"
    assert dataset.manifest.short_institution_name == "TEST"
    assert dataset.manifest.short_dataset_name == "Fixture"
    assert dataset.manifest.musicorpus_version == "1.0"


def test_the_folder_name_matches_the_manifest(dataset: Dataset) -> None:
    """What the specification requires of a conformant dataset."""
    manifest = dataset.manifest

    assert dataset.name == f"{manifest.short_institution_name}.{manifest.short_dataset_name}"


def test_load_rejects_a_folder_without_a_manifest() -> None:
    with pytest.raises(NotAMusicorpusDataset):
        Dataset.load(DATA / "not-a-dataset")


def test_load_rejects_a_folder_that_does_not_exist() -> None:
    with pytest.raises(NotAMusicorpusDataset):
        Dataset.load(DATA / "no-such-folder")


def test_find_all_skips_folders_that_are_not_datasets() -> None:
    found = Dataset.find_all(DATA)

    assert [d.name for d in found] == ["TEST.Fixture"]


def test_find_all_on_a_missing_root_is_empty() -> None:
    assert Dataset.find_all(DATA / "no-such-root") == []


def test_dataset_level_files(dataset: Dataset) -> None:
    assert dataset.readme_path is not None
    assert dataset.license_path is not None
    # the fixture ships neither of these, and asking must not raise
    assert dataset.coco_path is None
    assert dataset.specification_pdf_path is None
    assert dataset.coco() is None


# === pages ===


def test_page_names_lists_every_page_folder(dataset: Dataset) -> None:
    assert dataset.page_names == [
        "page-full",
        "page-images-only",
        "page-minimal",
        "page-outside-splits",
    ]


def test_pages_are_returned_in_name_order(dataset: Dataset) -> None:
    assert [page.name for page in dataset.pages()] == dataset.page_names


def test_a_page_knows_where_it_came_from(dataset: Dataset) -> None:
    page = dataset.page("page-full")

    assert isinstance(page, Page)
    assert page.name == "page-full"
    assert page.page_name == "page-full"
    assert page.dataset == dataset
    assert page.exists()


def test_a_page_that_is_not_on_disk(dataset: Dataset) -> None:
    """Asking for one is allowed; a splits file may name it."""
    page = dataset.page("page-missing-from-disk")

    assert not page.exists()
    assert page.image_path() is None
    assert page.transcription_formats() == []


def test_pages_compare_by_path(dataset: Dataset) -> None:
    assert dataset.page("page-full") == dataset.page("page-full")
    assert dataset.page("page-full") != dataset.page("page-minimal")
    assert len({dataset.page("page-full"), dataset.page("page-full")}) == 1


# === splits ===


def test_the_default_splits_file(dataset: Dataset) -> None:
    splits = dataset.splits()

    assert list(splits.split_names()) == ["train", "validation", "test"]
    assert splits.train == ["page-full", "page-minimal"]


def test_split_yields_pages_in_the_listed_order(dataset: Dataset) -> None:
    """The specification asks for splits to be shuffled, so order is data."""
    assert [page.name for page in dataset.split("train")] == ["page-full", "page-minimal"]


def test_splits_need_not_cover_every_page(dataset: Dataset) -> None:
    covered = set(dataset.splits().get_all_page_names())

    assert "page-outside-splits" in dataset.page_names
    assert "page-outside-splits" not in covered


def test_a_split_may_name_a_page_that_is_not_on_disk(dataset: Dataset) -> None:
    pages = list(dataset.split("test"))

    assert [page.name for page in pages] == ["page-missing-from-disk"]
    assert not pages[0].exists()


def test_alternative_splits_files_are_discovered(dataset: Dataset) -> None:
    assert dataset.split_variants() == ["alternative"]


def test_an_alternative_splits_file_can_add_sets(dataset: Dataset) -> None:
    splits = dataset.splits("alternative")

    assert "holdout" in list(splits.split_names())
    assert [page.name for page in dataset.split("holdout", "alternative")] == [
        "page-outside-splits"
    ]


# === images ===


def test_the_default_image(dataset: Dataset) -> None:
    path = dataset.page("page-full").image_path()

    assert path is not None
    assert path.name == "image.jpg"


def test_an_image_variant(dataset: Dataset) -> None:
    path = dataset.page("page-full").image_path("distorted")

    assert path is not None
    assert path.name == "image.distorted.jpg"


def test_a_missing_image_variant_is_none(dataset: Dataset) -> None:
    assert dataset.page("page-full").image_path("synthetic") is None


def test_image_variants_are_listed_without_the_default(dataset: Dataset) -> None:
    assert dataset.page("page-full").image_variants() == ["distorted"]
    assert dataset.page("page-minimal").image_variants() == []


def test_a_png_only_page_is_found_without_being_asked_for_png(dataset: Dataset) -> None:
    """The specification allows png and tif alongside the recommended jpg."""
    path = dataset.page("page-images-only").image_path()

    assert path is not None
    assert path.name == "image.png"


def test_asking_for_a_specific_suffix(dataset: Dataset) -> None:
    page = dataset.page("page-images-only")

    assert page.image_path(suffix="png") is not None
    assert page.image_path(suffix="jpg") is None


# === transcriptions ===


def test_transcription_paths(dataset: Dataset) -> None:
    page = dataset.page("page-full")

    assert page.transcription_path("musicxml") is not None
    assert page.transcription_path("krn") is not None
    assert page.transcription_path("mei") is None


def test_transcription_formats_lists_what_is_present(dataset: Dataset) -> None:
    assert dataset.page("page-full").transcription_formats() == ["musicxml", "krn"]
    assert dataset.page("page-minimal").transcription_formats() == ["musicxml"]
    assert dataset.page("page-images-only").transcription_formats() == []


# === subdivisions ===


def test_staves_and_grandstaves(dataset: Dataset) -> None:
    page = dataset.page("page-full")

    assert [s.name for s in page.staves] == ["1", "2"]
    assert [s.name for s in page.grandstaves] == ["1-2"]
    assert page.systems == []


def test_a_page_without_subdivisions(dataset: Dataset) -> None:
    page = dataset.page("page-minimal")

    assert page.staves == []
    assert page.grandstaves == []
    assert page.systems == []


def test_a_subdivision_knows_its_page_and_kind(dataset: Dataset) -> None:
    staff = dataset.page("page-full").staves[0]

    assert isinstance(staff, Subdivision)
    assert staff.kind == "Staves"
    assert staff.name == "1"
    assert staff.page_name == "page-full"
    assert staff.page == dataset.page("page-full")
    assert staff.dataset == dataset


def test_a_subdivision_carries_the_same_files_as_a_page(dataset: Dataset) -> None:
    staff = dataset.page("page-full").staves[0]

    assert staff.image_path() is not None
    assert staff.transcription_path("musicxml") is not None
    assert staff.transcription_formats() == ["musicxml", "krn"]


def test_subdivision_kinds_are_not_mistaken_for_pages(dataset: Dataset) -> None:
    """`Staves/` sits inside a page folder, not inside the dataset folder."""
    assert "Staves" not in dataset.page_names


# === the JSON formats MusiCorpus defines are parsed ===


def test_metadata_is_parsed(dataset: Dataset) -> None:
    metadata = dataset.page("page-full").metadata()

    assert isinstance(metadata, PageMetadata)
    assert metadata.notation == "CWMN"
    assert metadata.production == "printed"
    assert metadata.page_size == (210, 297)


def test_metadata_is_none_when_absent(dataset: Dataset) -> None:
    assert dataset.page("page-minimal").metadata() is None


def test_layout_is_parsed(dataset: Dataset) -> None:
    layout = dataset.page("page-full").layout()

    assert isinstance(layout, Layout)
    assert len(layout.staves) == 2
    assert len(layout.grandstaves) == 1
    assert layout.empty_staves == []
    assert layout.image_metadata.width == 64


def test_layout_is_none_when_absent(dataset: Dataset) -> None:
    assert dataset.page("page-minimal").layout() is None


def test_image_subdivisions_are_parsed(dataset: Dataset) -> None:
    subdivisions = dataset.page("page-full").image_subdivisions()

    assert isinstance(subdivisions, ImageSubdivisions)
    assert sorted(subdivisions.staves) == ["1", "2"]
    assert subdivisions.staves["1"].width == 56


def test_image_subdivisions_match_the_subdivision_folders(dataset: Dataset) -> None:
    """The mapping and the folders describe the same staves."""
    page = dataset.page("page-full")
    subdivisions = page.image_subdivisions()

    assert subdivisions is not None
    assert sorted(subdivisions.staves) == sorted(s.name for s in page.staves)
    assert sorted(subdivisions.grandstaves) == sorted(s.name for s in page.grandstaves)


def test_image_subdivisions_are_none_when_absent(dataset: Dataset) -> None:
    assert dataset.page("page-minimal").image_subdivisions() is None
    assert dataset.page("page-full").image_subdivisions("distorted") is None


# === the shape a consumer actually writes ===


def test_the_training_loop_a_consumer_writes(dataset: Dataset) -> None:
    """What Zeus hand-rolls across three modules today."""
    samples = [
        (sample.page_name, sample.kind, sample.name, path.name)
        for page in dataset.split("train")
        for sample in [*page.staves, *page.grandstaves]
        if (path := sample.transcription_path("musicxml")) is not None
    ]

    assert samples == [
        ("page-full", "Staves", "1", "transcription.musicxml"),
        ("page-full", "Staves", "2", "transcription.musicxml"),
        ("page-full", "Grandstaves", "1-2", "transcription.musicxml"),
    ]
