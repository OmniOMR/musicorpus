"""Tests for reading and writing `musicorpus.json`."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from musicorpus.manifest import MusicorpusManifest


def make_manifest(created_at: datetime) -> MusicorpusManifest:
    return MusicorpusManifest(
        musicorpus_version="1.0",
        full_institution_name="Test Institution",
        short_institution_name="TEST",
        institution_url="https://example.org",
        full_dataset_name="Test Dataset",
        short_dataset_name="Test",
        dataset_url="https://example.org/dataset",
        dataset_version="1.0",
        created_at=created_at,
        author_emails=["someone@example.org"],
    )


def test_a_written_manifest_can_be_read_back(tmp_path: Path) -> None:
    """The round trip broke on python 3.10, where `Z` was unparseable.

    `write_to_file` emits the `Z` designator the specification uses, and
    `datetime.fromisoformat` only accepted it from python 3.11 onwards — so
    this package could write a manifest it could not then read.
    """
    path = tmp_path / "musicorpus.json"
    written = make_manifest(datetime(2026, 3, 5, 10, 16, 37))
    written.write_to_file(path)

    read = MusicorpusManifest.load_from_file(path)

    assert read.short_institution_name == "TEST"
    assert read.short_dataset_name == "Test"
    assert read.created_at.replace(tzinfo=None) == written.created_at


def test_the_written_timestamp_keeps_the_specified_shape(tmp_path: Path) -> None:
    path = tmp_path / "musicorpus.json"
    make_manifest(datetime(2026, 3, 5, 10, 16, 37)).write_to_file(path)

    assert '"created_at": "2026-03-05T10:16:37Z"' in path.read_text()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-03-05T10:16:37Z", datetime(2026, 3, 5, 10, 16, 37, tzinfo=timezone.utc)),
        ("2026-03-05T10:16:37z", datetime(2026, 3, 5, 10, 16, 37, tzinfo=timezone.utc)),
        ("2026-03-05T10:16:37+00:00", datetime(2026, 3, 5, 10, 16, 37, tzinfo=timezone.utc)),
        (
            "2026-03-05T10:16:37+02:00",
            datetime(2026, 3, 5, 10, 16, 37, tzinfo=timezone(timedelta(hours=2))),
        ),
        ("2026-03-05T10:16:37", datetime(2026, 3, 5, 10, 16, 37)),
    ],
)
def test_created_at_accepts_the_iso_8601_spellings(value: str, expected: datetime) -> None:
    assert MusicorpusManifest.parse_created_at(value) == expected


def test_the_bundled_omniomr_manifest_parses() -> None:
    """The exporter ships a manifest asset; it has to be readable."""
    asset = Path(__file__).parent.parent / "src/musicorpus/exporters/omniomr/assets/musicorpus.json"

    manifest = MusicorpusManifest.load_from_file(asset)

    assert manifest.short_institution_name == "UFAL"
    assert manifest.short_dataset_name == "OmniOMR"
