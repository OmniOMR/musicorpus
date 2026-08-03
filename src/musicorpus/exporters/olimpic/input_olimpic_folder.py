"""Reads the OLiMPiC dataset as it is distributed, before any conversion.

Both distributed variants — scanned and synthetic — have the same shape:

    olimpic-1.0-scanned/
    ├── LICENSE
    ├── README.md
    ├── samples.dev.txt
    ├── samples.test.txt
    ├── samples.train.txt          (synthetic only)
    └── samples/
        └── 4919798/               a score
            ├── p1-s1.musicxml     page 1, system 1
            ├── p1-s1.png
            ├── p1-s1.lmx
            └── ...

A sample is one grandstaff: the system `s1` of the page `p1` of the score
`4919798`. The splits files list samples as `samples/{score}/p{page}-s{system}`,
one per line, in a shuffled order.
"""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

OlimpicVariant = Literal["scanned", "synthetic"]
"""Which of the two distributed OLiMPiC datasets is being read."""

SPLIT_NAMES: dict[str, str] = {
    "train": "train",
    "dev": "validation",
    "test": "test",
}
"""Maps a split as OLiMPiC names it onto the name MusiCorpus uses for it.

Only `dev` actually moves. The scanned variant ships no `train` split at all,
which is why the mapping is consulted rather than assumed.
"""


@dataclass(frozen=True)
class InputSample:
    """One OLiMPiC sample, which is one grandstaff of one page of one score."""

    score: str
    """Identifier of the score the sample was cut from, e.g. `4919798`.

    These come from the OpenScore Lieder corpus, of which OLiMPiC is a
    processed subset.
    """

    page: int
    """1-based number of the page within the score."""

    system: int
    """1-based number of the system within the page."""

    musicxml_path: Path
    """The grandstaff transcription, a single two-staff part."""

    image_path: Path
    """The grandstaff image, a `.png`."""

    @property
    def page_name(self) -> str:
        """The MusiCorpus page folder this sample belongs into, e.g. `4919798-p5`.

        OLiMPiC groups samples by score and names them by page; MusiCorpus is
        organised by page, so the two are folded together. This is the mapping
        the specification describes in Example 3.
        """
        return f"{self.score}-p{self.page}"

    @property
    def grandstaff_name(self) -> str:
        """The `Grandstaves/` folder this sample becomes, e.g. `2`.

        The specification recommends naming a grandstaff after the staves it
        spans (`1-2`, `3-4`), which needs the staff numbering of the original
        page. OLiMPiC pages were cut out of the Lieder corpus and that
        numbering did not survive, so the specification's fallback applies:
        number the grandstaves within the page from one. The system number
        already is that numbering.
        """
        return str(self.system)


class InputOlimpicFolder:
    """The untarred `olimpic-1.0-{variant}` folder, parsed."""

    def __init__(self, folder: Path, variant: OlimpicVariant):
        self.folder = folder
        self.variant: OlimpicVariant = variant

        self.samples_by_split: dict[str, list[InputSample]] = {}
        """Samples of each split, under the MusiCorpus split name, in the
        order the source file lists them (which is already shuffled)."""

        for olimpic_name, musicorpus_name in SPLIT_NAMES.items():
            splits_file = folder / f"samples.{olimpic_name}.txt"
            if not splits_file.exists():
                continue
            self.samples_by_split[musicorpus_name] = [
                self._parse_sample_line(line)
                for line in splits_file.read_text("utf-8").splitlines()
                if line.strip() != ""
            ]

        if len(self.samples_by_split) == 0:
            raise Exception(f"No samples.*.txt files found in: {folder}")

    def _parse_sample_line(self, line: str) -> InputSample:
        """Parses one `samples/{score}/p{page}-s{system}` line of a splits file."""
        relative_path = PurePosixPath(line.strip())
        score = relative_path.parent.name
        page_part, _, system_part = relative_path.name.partition("-")

        if not page_part.startswith("p") or not system_part.startswith("s"):
            raise Exception(f"Cannot parse the sample name {repr(line)}")

        return InputSample(
            score=score,
            page=int(page_part[1:]),
            system=int(system_part[1:]),
            musicxml_path=self.folder / f"{relative_path}.musicxml",
            image_path=self.folder / f"{relative_path}.png",
        )

    @property
    def license_path(self) -> Path:
        """The source `LICENSE` file, copied into the export as `LICENSE.txt`."""
        return self.folder / "LICENSE"

    def all_samples(self) -> list[InputSample]:
        """Every sample of every split, splits in the order they were read."""
        return [sample for samples in self.samples_by_split.values() for sample in samples]

    def page_names_by_split(self) -> dict[str, list[str]]:
        """The page names of each split, deduplicated, first appearance first.

        MusiCorpus splits pages where OLiMPiC splits grandstaves, so this only
        works because no OLiMPiC page has its systems spread across two splits
        — `check_that_it_covers_page_names_exactly` on the resulting splits
        would notice if that ever stopped holding, and `run_assertions` would
        catch the overlap.
        """
        return {
            split_name: list(dict.fromkeys(sample.page_name for sample in samples))
            for split_name, samples in self.samples_by_split.items()
        }
