from pathlib import Path
from ..ErrorBag import ErrorBag
import tqdm
import music21
import converter21
import traceback


def convert_musicxml_to_kern(
        output_folder: Path,
        errors: ErrorBag
):
    """Converts all .musicxml files in the dataset into .krn files"""
    converter21.register()

    for musicxml_path in tqdm.tqdm(
        list(output_folder.glob("**/*.musicxml")),
        "Converting MusicXML to Kern"
    ):
        relative_path = musicxml_path.relative_to(output_folder)
        page_name = relative_path.parts[0]
        
        kern_path = musicxml_path.with_suffix(".krn")
        
        try:
            parsed_musicxml = music21.converter.parse(musicxml_path)
            parsed_musicxml.write("humdrum", kern_path)
        except Exception:
            errors.add_error(
                page_name=page_name,
                message=f"Failed to convert MusicXML to Kern. " +
                f"In: {musicxml_path}\n" + traceback.format_exc()
            )
