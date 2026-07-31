from dataclasses import dataclass
from pathlib import Path
import csv


@dataclass
class LayoutRecord:
    """One record from the input page-layout CSV file"""
    
    page_name: str
    """The UUID_UUID name of a page"""

    staff_count: int
    """
    Safety check against MuNG files. Total number of staves on the page,
    including the empty ones. (basically the number of MuNG staff objects)
    """

    grandstaves: list[tuple[int, int]]
    """
    List of grandstaves, where each staff is a range tuple (from staff
    to staff) for the grandstaff and the range must be of length
    2 exactly. Staves are 1-indexed from top to bottom.

    Values look like: "1-2,3-4,6-7,8-9"

    Grandstaff is any two-staff that has a brace/bracket joining
    exactly those staves or is visibly a piano grandstaff from
    context (G-clef, F-clef combo; or they contain true pianoform
    music). This may include violins, but that's ok. If there are
    lyrics in between or the staves are unusually far apart,
    ignore those staves. If there are three or more braced staves,
    ignore them also. Grandstaff is only a pair of staves that
    really 'looks' like a piano grandstaff. If the two staves have
    music interacting with both (true pianoform music), it's also
    present in this list, but also present in the True Pianoform
    Staves field on the right.
    """

    true_pianoform_staves: list[tuple[int, int]]
    """
    A subset of Grandstaves that contain true pianoform music,
    meaning the music on the two staves interacts with both staves
    and cannot be losslessly split into two separate solo staves.
    (there's a beam or a stem across both staves, a voice transitioning
    to another staff making a gap in one staff should it be separated etc.)

    Values look like this: "1-2,3-4"
    """

    empty_staves: list[int]
    """
    Which staves are not transcribed to MusicXML, because they
    are empty filler staves. These may exist at the edge of
    the page or in between systems. In MuNG, these are annotated
    as staves with no content. We need to know about them,
    since they affect the staff index mapping between MuNG and MusicXML.

    Values look like: "1,2,8,9"
    """

    def __post_init__(self):
        assert self.staff_count > 0

        def _assert_staff_index(i: int):
            assert i >= 1 and i <= self.staff_count

        for r in self.grandstaves:
            assert r[1] - r[0] == 1, "Not a 2-staff range"
            _assert_staff_index(r[0])
            _assert_staff_index(r[1])
        
        for r in self.true_pianoform_staves:
            assert r[1] - r[0] == 1, "Not a 2-staff range"
            _assert_staff_index(r[0])
            _assert_staff_index(r[1])
            assert r in self.grandstaves, "Missing from grandstaves"
        
        for i in self.empty_staves:
            _assert_staff_index(i)
            assert i not in [b for r in self.grandstaves for b in r], \
                "Empty staves may not be present in grandstaves"


class InputLayoutFile:
    """
    Parsed representation of the input page-layout CSV file,
    which specifies which staves are grandstaves, empty, etc."""
    def __init__(self, records: list[LayoutRecord]):
        self.records: dict[str, LayoutRecord] = {
            record.page_name: record
            for record in records
        }
    
    @staticmethod
    def load(file_path: Path):
        records: list[LayoutRecord] = []
        with open(file_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # skip empty rows
                if row["Staff Count"] == "":
                    continue

                page_name = str(row["UUID"])
                staff_count = int(row["Staff Count"])
                records.append(LayoutRecord(
                    page_name=page_name,
                    staff_count=staff_count,
                    grandstaves=InputLayoutFile.parse_staff_range_list(
                        row["Grandstaves"]
                    ),
                    true_pianoform_staves=InputLayoutFile.parse_staff_range_list(
                        row["True Pianoform Staves"]
                    ),
                    empty_staves=InputLayoutFile.parse_staff_list(
                        row["Empty Staves"],
                        staff_count
                    )
                ))
        return InputLayoutFile(records)

    @staticmethod
    def parse_staff_list(text: str | None, staff_count: int) -> list[int]:
        if text is None or text.upper() == "NONE":
            return []
        
        if text == "ALL":
            return list(range(1, staff_count + 1))

        return [int(part.strip()) for part in text.split(",")]

    @staticmethod
    def parse_staff_range_list(text: str | None) -> list[tuple[int, int]]:
        if text is None or text.upper() == "NONE":
            return []
        
        def _parse_range(range_text: str) -> tuple[int, int]:
            bounds = range_text.split("-")
            assert len(bounds) == 2, \
                "Invalid range text: " + range_text
            return (int(bounds[0].strip()), int(bounds[1].strip()))
        
        return [
            _parse_range(part)
            for part in text.split(",")
        ]
