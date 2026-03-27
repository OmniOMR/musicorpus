from pathlib import Path
from ..ErrorBag import ErrorBag
from ..musescore_batch_convert import musescore_batch_convert


def convert_page_mscz_files_to_musicxml(
        page_names: list[str],
        output_folder: Path,
        errors: ErrorBag
):
    """
    Converts page-level .mscz files to .musicxml files using MuseScore.
    """
    print("Converting page-level .mscz files to .musicxml files...")
    
    # build up the conversion map (in path -> out path)
    conversion_map: dict[Path, Path] = {}
    for page_name in page_names:
        source_path = output_folder / page_name / "transcription.mscz"
        target_path = output_folder / page_name / "transcription.musicxml"

        if not source_path.exists():
            errors.add_error(
                page_name,
                "Source mscz file for conversion to musicxml missing at: " \
                    + str(source_path)
            )
            continue

        conversion_map[source_path] = target_path
    
    # run MuseScore
    musescore_batch_convert(
        conversion_map=conversion_map,
        force_replace_existing_files=True
    )
