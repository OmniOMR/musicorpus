"""Tests for reading and writing `layout.json`.

`layout.json` is a COCO file whose annotations are grouped by category into the
seven bbox lists `Layout` carries. Writing it was implemented long before
reading it, so the round trip is what these check.
"""

from datetime import datetime
from pathlib import Path

from musicorpus import CocoBbox, CocoDatasetMetadata, CocoImageMetadata, CocoLicense, Layout


def make_layout() -> Layout:
    return Layout(
        dataset_metadata=CocoDatasetMetadata(
            version="1.0",
            description="TEST.Fixture",
            contributor="Test Institution",
            url="https://example.org",
            date_created=datetime(2026, 3, 5),
        ),
        image_metadata=CocoImageMetadata(
            width=64,
            height=96,
            file_name="TEST.Fixture/page-full/image.jpg",
            date_captured=datetime(2026, 3, 5, 10, 16, 37),
        ),
        image_license=CocoLicense(name="CC BY 4.0", url="https://example.org/license"),
        staves=[CocoBbox(4, 8, 56, 16), CocoBbox(4, 40, 56, 16)],
        empty_staves=[CocoBbox(4, 60, 56, 16)],
        grandstaves=[CocoBbox(4, 8, 56, 48)],
        systems=[],
        staff_measures=[CocoBbox(4, 8, 28, 16)],
        grandstaff_measures=[],
        system_measures=[CocoBbox(0, 0, 64, 96)],
    )


def test_a_layout_survives_the_round_trip_through_json() -> None:
    layout = make_layout()

    assert Layout.parse_from_json(layout.serialize_to_json()) == layout


def test_a_layout_survives_the_round_trip_through_a_file(tmp_path: Path) -> None:
    layout = make_layout()
    path = tmp_path / "layout.json"
    layout.write_to_file(path)

    assert Layout.load_from_file(path) == layout


def test_each_bbox_list_keeps_its_own_category() -> None:
    """Staves must not come back as grandstaves."""
    parsed = Layout.parse_from_json(make_layout().serialize_to_json())

    assert parsed.staves == [CocoBbox(4, 8, 56, 16), CocoBbox(4, 40, 56, 16)]
    assert parsed.empty_staves == [CocoBbox(4, 60, 56, 16)]
    assert parsed.grandstaves == [CocoBbox(4, 8, 56, 48)]
    assert parsed.systems == []
    assert parsed.staff_measures == [CocoBbox(4, 8, 28, 16)]
    assert parsed.grandstaff_measures == []
    assert parsed.system_measures == [CocoBbox(0, 0, 64, 96)]


def test_an_unknown_category_is_skipped_rather_than_rejected() -> None:
    """A layout.json carrying extra annotations still reads."""
    data = make_layout().serialize_to_json()
    data["categories"].append({"id": 99, "name": "somethingElse"})
    data["annotations"].append(
        {
            "id": 999,
            "image_id": 0,
            "category_id": 99,
            "segmentation": [],
            "area": 1,
            "bbox": [1, 1, 1, 1],
            "iscrowd": 0,
        }
    )

    parsed = Layout.parse_from_json(data)

    assert parsed == make_layout()


def test_the_fixture_layout_reads() -> None:
    path = Path(__file__).parent / "data/TEST.Fixture/page-full/layout.json"

    layout = Layout.load_from_file(path)

    assert len(layout.staves) == 2
    assert layout.image_metadata.file_name == "page-full/image.jpg"


def test_coco_bboxes_compare_by_value() -> None:
    """Without this, every round-trip comparison above would be vacuous."""
    assert CocoBbox(1, 2, 3, 4) == CocoBbox(1, 2, 3, 4)
    assert CocoBbox(1, 2, 3, 4) != CocoBbox(1, 2, 3, 5)
    assert CocoBbox(1, 2, 3, 4) != "not a bbox"
    assert len({CocoBbox(1, 2, 3, 4), CocoBbox(1, 2, 3, 4)}) == 1
