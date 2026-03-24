from pathlib import Path
import tempfile
import json
import os
import requests


MSCORE_DOWNLOAD_URL = "https://github.com/musescore/MuseScore/releases/download/v4.6.5/MuseScore-Studio-4.6.5.253511702-x86_64.AppImage"
"URL from which MuseScore can be downloaded"

MSCORE: str = str((Path(__file__).parent.parent / "musescore" / "MuseScore-Studio-4.6.5.253511702-x86_64.AppImage").absolute())
"Absolute path to the MuseScore linux AppImage executable"


def musescore_to_mxl_conversion(
        mscz_paths: list[Path],
        target_format=".musicxml",
        replace_existing_files=True,
):
    """Executes MuseScore 4.6.5 to perform batch conversion
    of mscz files to MusicXML files."""

    download_musescore_if_missing()
    
    # create the conversion json file
    conversion = []
    for input_filepath in mscz_paths:
        assert input_filepath.exists(), \
            f"Input file {input_filepath} does not exist."
        output_filepath = input_filepath.with_suffix(target_format)

        # delete files to be replaced
        if output_filepath.exists() and replace_existing_files:
            output_filepath.unlink()
        
        # skip files that are already converted
        if output_filepath.exists():
            continue

        # make a record in the batch instruction for the file
        conversion.append({
            "in": str(input_filepath),
            "out": str(output_filepath)
        })
    
    # no conversions to be run, do nothing
    if len(conversion) == 0:
        return
    
    # run musescore conversion
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)
    try:
        json.dump(conversion, tmp)
        tmp.close()

        # clear musescore settings, since it may remember not to print
        # page and system breaks, but we do want those to be printed
        assert os.system(
            f"rm -f ~/.config/MuseScore/MuseScore3.ini"
        ) == 0
        assert os.system(
            f"rm -f ~/.config/MuseScore/MuseScore4.ini"
        ) == 0

        print("Running MusicXML conversion...")
        assert os.system(
            f"\"{MSCORE}\" -j \"{tmp.name}\""
        ) == 0
        print("Done.")
    finally:
        tmp.close()
        os.unlink(tmp.name)


def download_musescore_if_missing():
    if os.path.exists(MSCORE):
        return
    
    # download musescore
    print("Downloading MuseScore...")
    response = requests.get(MSCORE_DOWNLOAD_URL)
    with open(MSCORE, "wb") as f:
        f.write(response.content)
    print("Done.")

    # make it executable
    os.system(f"chmod +x \"{MSCORE}\"")
