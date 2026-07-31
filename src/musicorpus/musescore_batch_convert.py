import json
import os
import tempfile
from pathlib import Path

import requests

MSCORE_APPIMAGE = "MuseScore-Studio-4.6.5.253511702-x86_64.AppImage"
"File name of the MuseScore linux AppImage executable"

MSCORE_DOWNLOAD_URL = (
    "https://github.com/musescore/MuseScore/releases/download/v4.6.5/" + MSCORE_APPIMAGE
)
"URL from which MuseScore can be downloaded"

# Relative to the working directory, not to this file. It used to be
# `__file__.parent.parent`, which pointed at the repository root only because
# the code lived in `app/`; from `src/musicorpus/` it would point at `src/`,
# and from an installed package at site-packages. The CLI is documented as
# being run from the repository root, and `musescore/` there is gitignored,
# which is where this already downloaded to.
# TODO: lmx ships a `MuseScore` helper that does this properly, and lmx is
# already a dependency — this module should defer to it.
MSCORE: str = str((Path.cwd() / "musescore" / MSCORE_APPIMAGE).absolute())
"Absolute path to the MuseScore linux AppImage executable"


def musescore_batch_convert(
        conversion_map: dict[Path, Path],
        force_replace_existing_files=True,
):
    """Executes MuseScore 4.6.5 to perform batch conversion
    of files from one format to another depending on file suffixes."""

    download_musescore_if_missing()
    
    # create the conversion json file
    conversion = []
    for source_path, target_path in conversion_map.items():
        assert source_path.exists(), \
            f"Input file {source_path} does not exist."

        # delete files to be replaced
        if target_path.exists() and force_replace_existing_files:
            target_path.unlink()
        
        # skip files that are already converted
        if target_path.exists():
            continue

        # make a record in the batch instruction for the file
        conversion.append({
            "in": str(source_path),
            "out": str(target_path)
        })
    
    # no conversions to be run, do nothing
    if len(conversion) == 0:
        return
    
    # run musescore conversion
    # not a context manager on purpose: the file has to be closed and still
    # exist on disk while MuseScore reads it, and is unlinked in the `finally`
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)  # noqa: SIM115
    try:
        json.dump(conversion, tmp)
        tmp.close()

        # clear musescore settings, since it may remember not to print
        # page and system breaks, but we do want those to be printed
        assert os.system(
            "rm -f ~/.config/MuseScore/MuseScore3.ini"
        ) == 0
        assert os.system(
            "rm -f ~/.config/MuseScore/MuseScore4.ini"
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
    Path(MSCORE).parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(MSCORE_DOWNLOAD_URL)
    with open(MSCORE, "wb") as f:
        f.write(response.content)
    print("Done.")

    # make it executable
    os.system(f"chmod +x \"{MSCORE}\"")
