from pathlib import Path
from ..ErrorBag import ErrorBag
import tqdm
import music21
import converter21
import traceback
import shutil


def convert_musicxml_to_lilypond(
        output_folder: Path,
        errors: ErrorBag
):
    """Converts all .musicxml files in the dataset into .ly files"""
    converter21.register()

    assert shutil.which("lilypond") is not None, \
        "The 'lilypond' CLI command is not available on this machine.\n" + \
        "Install it with: sudo apt install lilypond"

    for musicxml_path in tqdm.tqdm(
        list(output_folder.glob("**/*.musicxml")),
        "Converting MusicXML to Lilypond"
    ):
        relative_path = musicxml_path.relative_to(output_folder)
        page_name = relative_path.parts[0]
        
        lilypond_path = musicxml_path.with_suffix(".ly")
        
        try:
            parsed_musicxml = music21.converter.parse(musicxml_path)
            parsed_musicxml.write("lilypond", lilypond_path)
        except Exception:
            errors.add_error(
                page_name=page_name,
                message=f"Failed to convert MusicXML to Lilypond. " +
                f"In: {musicxml_path}\n" + traceback.format_exc()
            )
