from pathlib import Path
import tarfile


def export_grandstaff(
        grandstaff_tgz_path: Path,
        output_folder: Path
):
    """
    Reads the `grandstaff.tgz` file and converts
    it into the MusiCorpus format with each sample
    being represented as one page.
    """

    # create the output folder
    output_folder.mkdir(parents=True)

    # The grandstaff.tgz contains files like these:
    # /beethoven
    # /chopin
    # /hummel
    #   /preludes
    #       /prelude67-01
    #           /original_m-56-60.jpg
    #
    # Which corresponds to this scheme:
    # {composer}/{genre}/{song}/original_m-{from}-{to}.jpg
    #
    # Where "original" means "no transposition was done",
    # and {from} and {to} are measure indexes within the song.
    #
    # This is based on the structure of KernScores from which
    # the GrandStaff dataset is created (https://kern.humdrum.org/)
    #
    # We can use this pattern to reorganize samples into pages
    # in the following way:
    #
    # Page:
    # {composer}_{song}/
    #   Grandstaves/
    #       original_m-56-60/
    #           image.jpg
    #           image_distorted.jpg
    #           transcription.krn
    #           transcription.musicxml
    #
    # Basically, each song becomes a MusiCorpus page and each
    # sample becomes one grandstaff subdivision of that page.
    # We explicitly omit the {genre} as it has minimal
    # informational value and only lengthens page names unnecessarily.
    #
    # We include all available transpositions, not just the "original".
    #
    # We include both .jpg and _distorted.jpg files and the .krn files.
    #
    # We include the .musicxml file from the Grandstaff LMX dataset at:
    # https://github.com/ufal/olimpic-icdar24/releases/tag/datasets
    # (must be added to CLI options)
    #
    # We do not provide Staff subdivisions, because it is unclear
    # as to where to get the images.

    print("To be implemented...")

    # this is how you can iterate a tgz archive:
    TAKE = 50
    taken = 0
    with tarfile.open(grandstaff_tgz_path, "r:gz") as archive:
        for member in archive:
            if member.isfile():
                stream = archive.extractfile(member)
                contents = b"" if stream is None else stream.read()
                print(str(len(contents)).zfill(10), "bytes of",member.name)
                taken += 1

                if taken >= TAKE:
                    break
