from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Any, get_args
import json


NotationType = Literal[
    "CWMN", "mensural", "square",
    "adiastematic", "instrument-specific", "other"
]

NotationComplexity = Literal[
    "monophonic", "homophonic", "polyphonic", "pianoform"
]

ProductionType = Literal[
    "printed", "handwritten", "born-digital"
]

NotationClarity = Literal[
    "perfect", "sufficient", "problematic", "unreadable"
]

SystemsComposition = Literal[
    "single-staff", "grand-staff", "multi-instrument", "variable"
]


@dataclass
class PageMetadata:
    """
    The metadata.json file present in each page.
    This is its python-parsed representation.
    """

    file_name: Path
    """Path to the image (relative to the root/ folder)
    this metadata file describes."""

    institution_name: str | Literal[False]
    """Human-readable name of the holding institution (library).
    Should be false for images that are born-digital
    and are not held by any institution."""

    institution_rism_siglum: str | None | Literal[False]
    """RISM assigns abbreviations to institutions holding
    musical works. This field should contain the siglum of
    the institution_name above. Should be null if the
    institution does not have a siglum yet. Should be
    false if the source document is not held in an institution."""

    institution_local_siglum: str | Literal[False]
    """The abbreviation by which the institution refers to itself.
    Should be false if the source document is not held in an institution."""

    shelfmark: str | None | Literal[False]
    """Identifies the source (manuscript, print, ...) within the
    institution's collection. Same as RISM shelfmark. Should be
    null if unknown. Should be false if the source document is
    not held in an institution."""

    rism_id_number: str | None | Literal[False]
    """If the source is catalogued in RISM, then this should be
    given. This field acts as a fallback if shelfmark does not
    exist. Should be false if not catalogued or null if unknown."""

    date: str | None
    """The year when was the source created. This can be very
    different from when the music therein was composed (e.g.
    20th century editions of Renaissance music). A specific year
    is usually very hard to pinpoint so instead this field is
    a string which allows for best-effort description of the year
    range if a singular year may not be pinned down.
    Should be null if unknown."""

    page_number: int | str | None
    """Some identification of the image within the source.
    Can be just a number, or foliation (e.g. f55v).
    Intended to be human-readable. Should be null if unknown."""

    page_size: tuple[int | None, int | None] | None
    """Size of the physical page/book in millimeters,
    [width, height]. It may be used to estimate DPI if
    DPI is not explicitly provided (with estimation error
    given by the margin around the page in the page scan image).
    Should be null if unknown. Also, individual dimensions may be
    null if only one dimension is known."""

    dpi: int | None
    """Actual DPI at which the image was scanned. Ideally
    as precise as possible - estimated via color calibration
    tables or rulers. Should be null if unknown."""

    scribal_data: int | str | None
    """Identifier of a handwriting/typesetting style (string
    or integer). May be used by a dataset intended for writer
    identification. Should be null if unknown or if not provided.
    Identifiers should be unique within the dataset."""

    link: str | None
    """URL to page image, if available. Prefer URL from holding
    institution, if not available, then other digitised version
    in RISM. Should be null if unknown or if such a link does
    not exist."""

    title_description: str | None | Literal[False]
    """Name of the composition (the musical piece captured
    within the document), e.g. "Sonata XYZ". Stick to RISM
    as much as possible. Should be null if unknown. Should
    be false if not aplicable (e.g. synthetic music)."""

    author: str | None | Literal[False]
    """Name of the composer, should be null if unknown.
    Should be false if not aplicable (e.g. synthetic music).
    Stick to RISM naming."""

    author_date: str | None | Literal[False]
    """Lifespan of the author, range of integers, e.g.
    1752-1832. Use ? if one of the dates is uncertain,
    e.g. ?-1832. Should be null if fully unknown.
    Should be false if not aplicable (e.g. synthetic
    music). Stick to RISM dating system."""

    genre_form: str | None
    """Human-readable, uncontrolled characterisation of
    the work, e.g. piano sonata, sting quartet, motet.
    Should be null if not provided."""

    notation: NotationType | None
    """Type of music notation. Must be one of: CWMN, mensural,
    square, adiastematic, instrument-specific, other.
    Should be null if unknown or not specified."""

    notation_detailed: str | None
    """Optional more fine-grained description, e.g. Black menusral,
    Suzipu, Franconian, German 16th c. lute tablature, Jeonggangbo,
    lead sheet, mountain hymnals, etc. Should be null if not specified."""

    notation_complexity: NotationComplexity | None
    """One of the four leves defined in the "Understanding OMR"
    paper. Must be one of: monophonic, homophonic, polyphonic,
    pianoform. Mark the page according to the most complex
    level that it contains -- for instance, the score of
    a piano concerto with just one grand staff with pianoform
    notation and everything else monophonic will be marked
    pianoform. The point is to signal "in order to recognise
    this page completely, one must account for this level of
    notation complexity". Should be null if not specified."""

    production: ProductionType | None
    """How was the music document created. Must be one of:
    printed, handwritten, born-digital. Should be null if
    not specified. Printed includes old printed scores
    as well as modern ink-jet printed and then scanned
    scores. Born-digital means being rendered by Verovio,
    Lilypond, MuseScore and other similar softwar
    directly to a JPEG/PNG file."""

    production_detailed: str | None
    """Optional more fine-grained description, e.g.:
    MuseScore, LilyPond with font..., movable type,
    sharpie marker, quill, etc. Should be null
    if not specified."""

    clarity: NotationClarity | None
    """The combined visual quality/readability of the page.
    There are four categories: perfect, sufficient,
    problematic, and unreadable. More discussion on this
    category, including criteria, in musicorpus specification.
    Should be null if not specified."""

    systems: SystemsComposition | None
    """Basic information about the relationship between
    staffs, systems, and reading order. Again, it serves
    as a signpost: "What do I have to care about when I
    use this dataset?" The field value is the answer to
    the question: "What does a single system of music
    consists of in this document?" Must be one of:
    single-staff, grand-staff, multi-instrument, variable.
    Should be null if not specified. If all systems on
    a page are of one type (single-staff, grand-staff,
    multi-instument), then that type is the value of this
    field. If there is at least one system of different
    type (e.g. when there are multiple songs within one
    page with different setup), then variable should be
    used."""

    @staticmethod
    def load_from_file(file_path: Path) -> "PageMetadata":
        with open(file_path, "r") as f:
            data = json.load(f)
        return PageMetadata.parse_from_json(data)

    @staticmethod
    def parse_from_json(data: dict) -> "PageMetadata":
        def str_n(v) -> str | None:
            if v is None: return None
            return str(v)
        
        def str_f(v) -> str | Literal[False]:
            if v is False: return False
            return str(v)
        
        def str_nf(v) -> str | None | Literal[False]:
            if v is None: return None
            if v is False: return False
            return str(v)
        
        def int_n(v) -> int | None:
            if v is None: return None
            return int(v)
        
        def int_str_n(v) -> int | str | None:
            if v is None: return None
            if type(v) is int: return v
            return str(v)
        
        def lit(t, v) -> Any | None:
            values: tuple[str] = get_args(t) # args to Literal[...]
            if v in values: return v
            if v is None: return None
            raise Exception(f"Value {repr(v)} must be one of {repr(values)}")
        
        if data["page_size"] is not None:
            page_size = tuple(data["page_size"])
            assert len(page_size) == 2
            page_size = tuple(
                int(i) if i is not None else None
                for i in page_size
            )
        else:
            page_size = None

        return PageMetadata(
            file_name=Path(data["file_name"]),
            institution_name=str_f(data["institution_name"]),
            institution_rism_siglum=str_nf(data["institution_rism_siglum"]),
            institution_local_siglum=str_f(data["institution_local_siglum"]),
            shelfmark=str_nf(data["shelfmark"]),
            rism_id_number=str_nf(data["rism_id_number"]),
            date=str_n(data["date"]),
            page_number=int_str_n(data["page_number"]),
            page_size=page_size,
            dpi=int_n(data["dpi"]),
            scribal_data=int_str_n(data["scribal_data"]),
            link=str_n(data["link"]),
            title_description=str_nf(data["title_description"]),
            author=str_nf(data["author"]),
            author_date=str_nf(data["author_date"]),
            genre_form=str_n(data["genre_form"]),
            notation=lit(NotationType, data["notation"]),
            notation_detailed=str_n(data["notation_detailed"]),
            production=lit(ProductionType, data["production"]),
            production_detailed=str_n(data["production_detailed"]),
            notation_complexity=lit(NotationComplexity, data["notation_complexity"]),
            clarity=lit(NotationClarity, data["clarity"]),
            systems=lit(SystemsComposition, data["systems"])
        )

    def serialize_to_json(self) -> dict:
        return {
            "file_name": self.file_name.as_posix(),
            "institution_name": self.institution_name,
            "institution_rism_siglum": self.institution_rism_siglum,
            "institution_local_siglum": self.institution_local_siglum,
            "shelfmark": self.shelfmark,
            "rism_id_number": self.rism_id_number,
            "date": self.date,
            "page_number": self.page_number,
            "page_size": self.page_size,
            "dpi": self.dpi,
            "scribal_data": self.scribal_data,
            "link": self.link,
            "title_description": self.title_description,
            "author": self.author,
            "author_date": self.author_date,
            "genre_form": self.genre_form,
            "notation": self.notation,
            "notation_detailed": self.notation_detailed,
            "production": self.production,
            "production_detailed": self.production_detailed,
            "notation_complexity": self.notation_complexity,
            "clarity": self.clarity,
            "systems": self.systems
        }

    def write_to_file(self, file_path: Path):
        with open(file_path, "w") as f:
            data = self.serialize_to_json()
            json.dump(data, f, indent=2)
