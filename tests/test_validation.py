"""Tests for `musicorpus validate`, against the two committed fixtures.

`TEST.Valid` conforms to the specification in every respect the validator
checks, so it must produce no errors at all. Each test that expects an error
copies it and breaks exactly one thing, which is what keeps the assertions
about the check under test rather than about the fixture.

`TEST.Fixture` is the reader's fixture and deliberately does not conform; the
last test pins what the validator says about it, so that a change in either
one is noticed.

These need the `validation` extra. The base install has no mung, no
pycocotools and no lmx, and cannot run the validator at all.
"""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from musicorpus import ErrorBag

# The validator lives behind the `validation` extra, and importing it without
# that extra installed is a collection error rather than a useful message.
pytest.importorskip("mung", reason="these tests need the 'validation' extra")

from musicorpus.validation.validate_dataset import validate_dataset  # noqa: E402

DATA = Path(__file__).parent / "data"
VALID = DATA / "TEST.Valid"
READER_FIXTURE = DATA / "TEST.Fixture"


def validate(dataset_path: Path) -> ErrorBag:
    errors = ErrorBag()
    validate_dataset(dataset_path=dataset_path, errors=errors)
    return errors


def messages(errors: ErrorBag) -> str:
    return "\n".join(errors.log)


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    """A writable copy of the conformant fixture, to be broken by one test."""
    target = tmp_path / VALID.name
    shutil.copytree(VALID, target)
    return target


# === the baseline ===


def test_a_conformant_dataset_produces_no_errors() -> None:
    errors = validate(VALID)

    assert errors.count == 0, messages(errors)
    assert errors.affected_pages == []


def test_the_conformant_fixture_is_what_it_claims_to_be(dataset: Path) -> None:
    """A copy of it is still clean — the tests below start from zero."""
    assert validate(dataset).count == 0


# === root files ===


def break_it(dataset: Path, action: Callable[[Path], object]) -> ErrorBag:
    """Applies one mutation to the copied dataset, then validates it.

    The return type is `object` rather than `None` because the mutations are
    mostly one-line lambdas over `write_text` and `shutil.copy`, which return
    a count and a path; what they return is not used.
    """
    action(dataset)
    return validate(dataset)


def test_a_missing_specification_pdf_is_reported(dataset: Path) -> None:
    errors = break_it(dataset, lambda d: (d / "musicorpus-specification.pdf").unlink())

    assert errors.count == 1
    assert "musicorpus-specification.pdf" in messages(errors)


def test_a_missing_readme_is_reported(dataset: Path) -> None:
    errors = break_it(dataset, lambda d: (d / "README.md").unlink())

    assert errors.count == 1
    assert "README.md" in messages(errors)


def test_a_missing_license_is_reported(dataset: Path) -> None:
    errors = break_it(dataset, lambda d: (d / "LICENSE.txt").unlink())

    assert errors.count == 1
    assert "LICENSE.txt" in messages(errors)


def test_a_missing_manifest_stops_the_validation(dataset: Path) -> None:
    """Nothing further can be checked without it, so it must be the only error."""
    errors = break_it(dataset, lambda d: (d / "musicorpus.json").unlink())

    assert errors.count == 1
    assert "musicorpus.json" in messages(errors)


def test_a_folder_name_that_disagrees_with_the_manifest_is_reported(
    dataset: Path, tmp_path: Path
) -> None:
    """Renaming the folder also invalidates every `metadata.json`.

    Those carry a `file_name` relative to the root folder, so it begins with
    the dataset folder's name — three errors here rather than one, and all
    three are the truth.
    """
    renamed = tmp_path / "WRONG.Name"
    dataset.rename(renamed)

    errors = validate(renamed)

    assert "should be called TEST.Valid" in messages(errors)
    assert messages(errors).count("file_name") == 2


# === splits ===


def test_splits_that_miss_a_page_are_reported(dataset: Path) -> None:
    errors = break_it(
        dataset,
        lambda d: (d / "splits.json").write_text('{"train": ["page-one"], "test": []}'),
    )

    assert errors.count == 1
    assert "splits.json" in messages(errors)


def test_splits_that_name_an_unknown_page_are_reported(dataset: Path) -> None:
    errors = break_it(
        dataset,
        lambda d: (d / "splits.json").write_text(
            '{"train": ["page-one", "page-nine"], "validation": ["page-two"], "test": []}'
        ),
    )

    assert errors.count == 1
    assert "splits.json" in messages(errors)


def test_overlapping_splits_are_reported(dataset: Path) -> None:
    errors = break_it(
        dataset,
        lambda d: (d / "splits.json").write_text(
            '{"train": ["page-one", "page-two"], "validation": ["page-two"], "test": []}'
        ),
    )

    assert errors.count == 1
    assert "splits.json" in messages(errors)


def test_an_alternative_splits_file_is_validated_too(dataset: Path) -> None:
    errors = break_it(
        dataset,
        lambda d: (d / "splits.book-consistent.json").write_text(
            '{"train": ["page-nine"], "validation": [], "test": []}'
        ),
    )

    assert errors.count == 1
    assert "splits.book-consistent.json" in messages(errors)


# === folder homogeneity ===


def test_a_page_missing_a_file_the_others_have_is_reported(dataset: Path) -> None:
    errors = break_it(dataset, lambda d: (d / "page-two/metadata.json").unlink())

    assert errors.count == 1
    assert "Missing metadata.json" in messages(errors)
    assert errors.affected_pages == ["page-two"]


def test_a_subdivision_missing_a_file_the_others_have_is_reported(dataset: Path) -> None:
    """Deleting the image also breaks the bbox check that measures it."""
    errors = break_it(dataset, lambda d: (d / "page-one/Staves/1/image.jpg").unlink())

    assert "Missing image.jpg" in messages(errors)
    assert "does not match the subdivision image" in messages(errors)


def test_page_level_metadata_inside_a_subdivision_is_reported(dataset: Path) -> None:
    def add_metadata_to_every_staff(d: Path) -> None:
        source = d / "page-one/metadata.json"
        for staff in d.glob("*/Staves/*"):
            shutil.copy(source, staff / "metadata.json")

    errors = break_it(dataset, add_metadata_to_every_staff)

    assert "should only be present in page folders" in messages(errors)


# === blacklisted file names ===


@pytest.mark.parametrize(
    ("wrong_name", "right_name"),
    [
        ("image.jpeg", "image.jpg"),
        ("transcription.mxl", "transcription.musicxml"),
        ("transcription.xml", "transcription.musicxml"),
        ("transcription.kern", "transcription.krn"),
    ],
)
def test_a_misnamed_file_is_reported(dataset: Path, wrong_name: str, right_name: str) -> None:
    """These names are close enough to the right ones to be worth catching."""

    def rename_in_every_page(d: Path) -> None:
        for page in ["page-one", "page-two"]:
            source = d / page / right_name
            if not source.exists():
                source = d / page / "image.jpg"
            shutil.copy(source, d / page / wrong_name)

    errors = break_it(dataset, rename_in_every_page)

    assert wrong_name in messages(errors)


# === file contents ===


def test_a_broken_musicxml_file_is_reported(dataset: Path) -> None:
    errors = break_it(
        dataset,
        lambda d: (d / "page-one/transcription.musicxml").write_text("this is not xml"),
    )

    assert errors.count == 1
    assert "cannot be loaded" in messages(errors)


def test_a_musicxml_without_declared_system_breaks_is_reported(dataset: Path) -> None:
    """The specification asks for line breaks to be explicit."""

    def strip_the_supports_declaration(d: Path) -> None:
        path = d / "page-one/transcription.musicxml"
        text = path.read_text()
        start, end = text.index("<identification>"), text.index("</identification>")
        path.write_text(text[:start] + text[end + len("</identification>") :])

    errors = break_it(dataset, strip_the_supports_declaration)

    assert errors.count == 1
    assert "Failed to load MusicXML layout" in messages(errors)


def test_a_multi_system_musicxml_in_a_subdivision_is_reported(dataset: Path) -> None:
    """A subdivision holds one system by definition."""
    errors = break_it(
        dataset,
        lambda d: shutil.copy(
            d / "page-one/transcription.musicxml",  # the page-level one has two systems
            d / "page-one/Staves/1/transcription.musicxml",
        ),
    )

    assert errors.count == 1
    assert "must be single-system" in messages(errors)


def test_a_broken_metadata_file_is_reported(dataset: Path) -> None:
    errors = break_it(
        dataset,
        lambda d: (d / "page-one/metadata.json").write_text('{"notation": "not-a-notation-type"}'),
    )

    assert errors.count > 0
    assert "notation" in messages(errors)


def test_a_layout_pointing_at_a_missing_image_is_reported(dataset: Path) -> None:
    def repoint_the_layout(d: Path) -> None:
        path = d / "page-one/layout.json"
        path.write_text(path.read_text().replace("page-one/image.jpg", "page-one/nope.jpg"))

    errors = break_it(dataset, repoint_the_layout)

    assert errors.count > 0
    assert "nope.jpg" in messages(errors)


def test_a_layout_with_the_wrong_image_size_is_reported(dataset: Path) -> None:
    def resize_the_layout(d: Path) -> None:
        path = d / "page-one/layout.json"
        path.write_text(path.read_text().replace('"width": 64', '"width": 999'))

    errors = break_it(dataset, resize_the_layout)

    assert errors.count > 0
    assert "999" in messages(errors)


# === the deliberately non-conformant reader fixture ===


def test_the_reader_fixture_reports_only_its_known_deviations() -> None:
    """It bends the rules on purpose; this pins exactly how.

    Every error is structural — a missing root file, splits that do not cover
    the pages, or pages that do not carry the same files as each other. None
    is about the contents of a file, which is what makes it a usable fixture
    for the reader tests.
    """
    errors = validate(READER_FIXTURE)
    log = messages(errors)

    assert "musicorpus-specification.pdf" in log
    assert "The splits.json file has an issue" in log
    assert "Missing" in log

    for phrase in [
        "cannot be loaded",
        "Failed to load MusicXML layout",
        "does not exist",
        "must be single-system",
    ]:
        assert phrase not in log, f"unexpected content error in the reader fixture: {phrase}"
