"""Regenerates the `TEST.Fixture` dataset that the tests read.

The fixture is committed rather than built during the test run, so that it can
be inspected, diffed and pointed at as a worked example of the layout. This
script is how it was produced, and re-running it must leave the tree unchanged:

    .venv/bin/python tests/data/build_test_fixture.py
    git status --short tests/data

Every file it writes goes through this package's own writers wherever one
exists, so the fixture cannot claim a shape the library does not produce.

The fixture deliberately includes the awkward cases: a page with nothing but an
image and a transcription, a page that no split mentions, a split that names a
page which is not on disk, an image variant, and an alternative splits file.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from musicorpus.coco import CocoBbox, CocoDatasetMetadata, CocoImageMetadata, CocoLicense
from musicorpus.image_subdivisions import ImageSubdivisions
from musicorpus.layout import Layout
from musicorpus.manifest import MusicorpusManifest
from musicorpus.page_metadata import PageMetadata
from musicorpus.splits import Splits

HERE = Path(__file__).parent
DATASET = HERE / "TEST.Fixture"
VALID = HERE / "TEST.Valid"

CREATED_AT = datetime(2026, 3, 5, 10, 16, 37)


def musicxml(systems: int = 1) -> str:
    """A minimal but conformant MusicXML document with the given system count.

    The specification asks for line breaks to be encoded explicitly with
    `<print new-system="yes">`, and lmx refuses a document whose
    `<identification><encoding><supports>` does not say so. The marker means
    "a break happens *before* this measure", so the first measure carries none
    — lmx counts the opening system implicitly, and a break there would claim
    an empty system before it.
    """
    measures = []
    for index in range(systems):
        measures.append(
            f"""    <measure number="{index + 1}">
      {'<print new-system="yes"/>' if index > 0 else ""}
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration><type>whole</type>
      </note>
    </measure>"""
        )
    body = "\n".join(measures)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <identification>
    <encoding>
      <software>tests/data/build_test_fixture.py</software>
      <supports element="print" attribute="new-system" type="yes" value="yes"/>
      <supports element="print" attribute="new-page" type="yes" value="yes"/>
    </encoding>
  </identification>
  <part-list>
    <score-part id="P1"><part-name>Music</part-name></score-part>
  </part-list>
  <part id="P1">
{body}
  </part>
</score-partwise>
"""


KERN = """**kern
*clefG2
*k[]
*M4/4
1c
*-
"""


def write_image(path: Path, width: int, height: int) -> None:
    """A real JPEG, small but decodable, so image tests are not built on a lie."""
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    image[height // 2 : height // 2 + 2, :, :] = 0  # a staff-line-ish stripe
    path.parent.mkdir(parents=True, exist_ok=True)
    assert cv2.imwrite(str(path), image), f"could not write {path}"


def write_sample(
    folder: Path, width: int, height: int, kern: bool = False, systems: int = 1
) -> None:
    """The files a page or a subdivision carries."""
    folder.mkdir(parents=True, exist_ok=True)
    write_image(folder / "image.jpg", width, height)
    (folder / "transcription.musicxml").write_text(musicxml(systems))
    if kern:
        (folder / "transcription.krn").write_text(KERN)


def page_metadata(page_name: str, dataset: str = "TEST.Fixture") -> PageMetadata:
    """`metadata.json`'s `file_name` is relative to the root/ folder, so it
    carries the dataset folder name — unlike COCO's, which is relative to the
    dataset folder. The specification states both, in different sections."""
    return PageMetadata(
        file_name=Path(dataset) / page_name / "image.jpg",
        institution_name="Test Library",
        institution_rism_siglum="CZ-Tl",
        institution_local_siglum="TL",
        shelfmark="TL 1234",
        rism_id_number=None,
        date="1780",
        page_number=1,
        page_size=(210, 297),
        dpi=300,
        scribal_data=None,
        link="https://example.org/source",
        title_description="A test page",
        author="Anonymous",
        author_date=None,
        genre_form="sonata",
        notation="CWMN",
        notation_detailed=None,
        notation_complexity="polyphonic",
        production="printed",
        production_detailed=None,
        clarity="perfect",
        systems="grand-staff",
    )


def build_reader_fixture() -> None:
    if DATASET.exists():
        shutil.rmtree(DATASET)
    DATASET.mkdir(parents=True)

    # === dataset-level files ===

    MusicorpusManifest(
        musicorpus_version="1.0",
        full_institution_name="Test Institution",
        short_institution_name="TEST",
        institution_url="https://example.org",
        full_dataset_name="MusiCorpus Test Fixture",
        short_dataset_name="Fixture",
        dataset_url="https://example.org/fixture",
        dataset_version="1.0",
        created_at=CREATED_AT,
        author_emails=["someone@example.org", "someone-else@example.org"],
    ).write_to_file(DATASET / "musicorpus.json")

    (DATASET / "README.md").write_text(
        "# MusiCorpus Test Fixture\n"
        "\n"
        "A tiny synthetic dataset used by this repository's tests. It is not real\n"
        "data — the images are blank rectangles and the transcriptions hold a\n"
        "single whole note — but its structure is exactly what the MusiCorpus\n"
        "specification asks for, so it doubles as a worked example of the layout.\n"
        "\n"
        "It is generated by `tests/data/build_test_fixture.py`.\n"
        "\n"
        "\n"
        "## Splits\n"
        "\n"
        "`splits.json` is a plain train/validation/test division. It deliberately\n"
        "does not cover every page: `page-outside-splits` is in no split, which\n"
        "the specification permits. `splits.alternative.json` covers the same\n"
        "pages differently and adds a `holdout` set.\n"
    )
    (DATASET / "LICENSE.txt").write_text(
        "This fixture contains no real data and is released under the same terms\n"
        "as the repository that holds it.\n"
    )

    # === splits ===

    Splits(
        train=["page-full", "page-minimal"],
        validation=["page-images-only"],
        test=["page-missing-from-disk"],
    ).write_to_file(DATASET / "splits.json", run_assertions=False)

    Splits(
        train=["page-full"],
        validation=["page-minimal"],
        test=["page-images-only"],
        holdout=["page-outside-splits"],
    ).write_to_file(DATASET / "splits.alternative.json", run_assertions=False)

    # === page-full: every optional file, both subdivision kinds ===

    page = DATASET / "page-full"
    write_sample(page, width=64, height=96, kern=True, systems=2)
    write_image(page / "image.distorted.jpg", 64, 96)
    page_metadata("page-full").write_to_file(page / "metadata.json")

    staff_bboxes = {"1": CocoBbox(4, 8, 56, 16), "2": CocoBbox(4, 40, 56, 16)}
    grandstaff_bboxes = {"1-2": CocoBbox(4, 8, 56, 48)}
    ImageSubdivisions(
        staves=staff_bboxes,
        grandstaves=grandstaff_bboxes,
        systems={},
    ).write_to(page / "subdivisions.image.json")

    Layout(
        dataset_metadata=CocoDatasetMetadata(
            version="1.0",
            description="TEST.Fixture",
            contributor="Test Institution",
            url="https://example.org/fixture",
            date_created=CREATED_AT,
        ),
        image_metadata=CocoImageMetadata(
            width=64,
            height=96,
            file_name="page-full/image.jpg",
            date_captured=CREATED_AT,
        ),
        image_license=CocoLicense(name="CC BY 4.0", url="https://example.org/license"),
        staves=list(staff_bboxes.values()),
        empty_staves=[],
        grandstaves=list(grandstaff_bboxes.values()),
        systems=[],
        staff_measures=[],
        grandstaff_measures=[],
        system_measures=[],
    ).write_to_file(page / "layout.json")

    for name in staff_bboxes:
        write_sample(page / "Staves" / name, width=56, height=16, kern=True)
    for name in grandstaff_bboxes:
        write_sample(page / "Grandstaves" / name, width=56, height=48)

    # === page-minimal: an image and a transcription, nothing else ===

    write_sample(DATASET / "page-minimal", width=64, height=96)

    # === page-images-only: an image, no transcription, a PNG rather than a JPEG ===

    images_only = DATASET / "page-images-only"
    images_only.mkdir()
    write_image(images_only / "image.png", 64, 96)

    # === page-outside-splits: on disk, named by no split in splits.json ===

    write_sample(DATASET / "page-outside-splits", width=64, height=96)

    print(f"wrote {DATASET}")
    print(f"  {sum(1 for _ in DATASET.rglob('*') if _.is_file())} files")


def minimal_pdf() -> bytes:
    """A real, openable one-page PDF, so the fixture ships no fake file.

    `musicorpus validate` only checks that the specification PDF is present,
    but a file called `.pdf` that no reader can open would be a lie sitting in
    a fixture other people are invited to copy. The cross-reference offsets
    are computed rather than guessed, which is the only fiddly part.
    """
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"

    xref_offset = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objects) + 1)
    out += b"startxref\n%d\n%%%%EOF\n" % xref_offset
    return bytes(out)


def build_valid_fixture() -> None:
    """A strictly conformant dataset: `musicorpus validate` must find nothing.

    Everything the reader fixture bends on purpose is straight here — the
    splits cover the pages exactly, every page carries the same files, every
    staff folder carries the same files, and the specification PDF is present.
    It is the baseline the validator tests mutate.
    """
    if VALID.exists():
        shutil.rmtree(VALID)
    VALID.mkdir(parents=True)

    page_names = ["page-one", "page-two"]

    MusicorpusManifest(
        musicorpus_version="1.0",
        full_institution_name="Test Institution",
        short_institution_name="TEST",
        institution_url="https://example.org",
        full_dataset_name="MusiCorpus Valid Fixture",
        short_dataset_name="Valid",
        dataset_url="https://example.org/valid",
        dataset_version="1.0",
        created_at=CREATED_AT,
        author_emails=["someone@example.org"],
    ).write_to_file(VALID / "musicorpus.json")

    (VALID / "README.md").write_text(
        "# MusiCorpus Valid Fixture\n"
        "\n"
        "A tiny synthetic dataset that conforms to the MusiCorpus specification\n"
        "in every respect the validator checks, so that `musicorpus validate`\n"
        "reports no errors on it. The validator tests copy it and break one\n"
        "thing at a time.\n"
        "\n"
        "It is generated by `tests/data/build_test_fixture.py`.\n"
    )
    (VALID / "LICENSE.txt").write_text(
        "This fixture contains no real data and is released under the same terms\n"
        "as the repository that holds it.\n"
    )
    (VALID / "musicorpus-specification.pdf").write_bytes(minimal_pdf())

    Splits(
        train=["page-one"],
        validation=["page-two"],
        test=[],
    ).write_to_file(VALID / "splits.json", run_assertions=False)

    for page_name in page_names:
        page = VALID / page_name
        write_sample(page, width=64, height=96, systems=2)
        page_metadata(page_name, dataset="TEST.Valid").write_to_file(page / "metadata.json")

        staff_bboxes = {"1": CocoBbox(4, 8, 56, 16), "2": CocoBbox(4, 40, 56, 16)}
        ImageSubdivisions(staves=staff_bboxes).write_to(page / "subdivisions.image.json")

        Layout(
            dataset_metadata=CocoDatasetMetadata(
                version="1.0",
                description="TEST.Valid",
                contributor="Test Institution",
                url="https://example.org/valid",
                date_created=CREATED_AT,
            ),
            image_metadata=CocoImageMetadata(
                width=64,
                height=96,
                file_name=f"{page_name}/image.jpg",
                date_captured=CREATED_AT,
            ),
            image_license=CocoLicense(name="CC BY 4.0", url="https://example.org/license"),
            staves=list(staff_bboxes.values()),
            empty_staves=[],
            grandstaves=[],
            systems=[],
            staff_measures=[],
            grandstaff_measures=[],
            system_measures=[],
        ).write_to_file(page / "layout.json")

        for name in staff_bboxes:
            write_sample(page / "Staves" / name, width=56, height=16)

    print(f"wrote {VALID}")
    print(f"  {sum(1 for _ in VALID.rglob('*') if _.is_file())} files")


def build_non_dataset() -> None:
    other = HERE / "not-a-dataset"
    other.mkdir(exist_ok=True)
    (other / "README.md").write_text(
        "Deliberately not a MusiCorpus dataset: it holds no musicorpus.json,\n"
        "so `Dataset.find_all` must skip it.\n"
    )


if __name__ == "__main__":
    build_reader_fixture()
    build_valid_fixture()
    build_non_dataset()
    # a sanity check that what was written reads back
    from musicorpus import Dataset

    dataset = Dataset.load(DATASET)
    print(f"  manifest: {dataset.manifest.full_dataset_name}")
    print(f"  pages:    {dataset.page_names}")
    print(f"  splits:   {list(dataset.splits().split_names())}")
    manifest_json = json.loads((DATASET / "musicorpus.json").read_text())
    print(f"  json ok:  musicorpus_version {manifest_json['musicorpus_version']}")
