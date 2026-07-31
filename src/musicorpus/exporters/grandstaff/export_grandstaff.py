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
    # {composer}/{genre}/{song}/{transposition}_m-{from}-{to}.jpg
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
    # {composer}_{song}_{transposition}_m-{from}-{to}/
    #   Grandstaves/
    #       1-2/                        (only one grandstaff per "page")
    #           image.jpg
    #           image.distorted.jpg
    #           transcription.krn
    #           transcription.musicxml
    #
    # Basically, each sample becomes a MusiCorpus page with
    # exactly one grandstaff subdivision of that page being that sample.
    # We explicitly omit the {genre} as it has minimal
    # informational value and only lengthens page names unnecessarily.
    #
    # We include all available transpositions, not just the "original".
    #
    # We include both .jpg and .distorted.jpg files and the .krn files.
    #
    # We include the .musicxml file from the Grandstaff LMX dataset at:
    # https://github.com/ufal/olimpic-icdar24/releases/tag/datasets
    # (must be added to CLI options)
    #
    # We do NOT provide Staff subdivisions, because it is unclear
    # as to where to get the images.
    #
    # The splits.json file should be generated from
    # samples.train/dev/test.txt files in the GrandStaff-LMX dataset.
    # These were requested from the original GrandStaff paper authors
    # and should correspond to their partitioning of the dataset.
    # The official grandstaff.tgz file unfortunately does not
    # contain these partitions.
    #
    # We decided to have one musicorpus page as one grandstaff sample,
    # so that splits.json file could be provided. It would be semantically
    # nicer to have one grandstaff song to become one musicorpus page,
    # however that would require the slits.json to be song-consistent,
    # which it isn't. We also discovered that there's an overlap not
    # only in songs between train/test but also in measure ranges.
    # However they always come from a different transposition.
    # The test split contains ONLY "original" transpositions,
    # while the augmented data is present in train and dev.
    #
    # The resulting PRAIG.GrandStaff folder will therefore contain
    # cca 40K folders (pages = samples). While this is a lot and
    # will cause slowdowns in file explorers, it is doable.
    # The PrIMuS dataset developed by the same group as GrandStaff
    # is disctributed as a .tgz archive with over 86K folders in
    # the top-level folder.

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
