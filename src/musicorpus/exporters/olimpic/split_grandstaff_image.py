"""Cuts a grandstaff image into an upper-staff and a lower-staff image."""

import numpy as np

OVERLAP_FRACTION = 2 / 3
"""How much of the grandstaff's height each of the two staff images keeps.

Two thirds, so the two crops overlap in the middle third rather than meeting
at a seam. A staff is not just its five lines: stems, beams, slurs and ledger
lines reach well past them, and a note belonging to the upper staff may be
drawn below the upper staff's bottom line. Cutting at the exact halfway point
would slice those off. The overlap costs some of the other staff appearing at
the edge of the crop, which is the cheaper mistake — the model sees context it
must learn to ignore rather than losing notation it is asked to transcribe.

This is a heuristic. OLiMPiC carries no staff coordinates, so there is nothing
to cut precisely against.
"""


def split_grandstaff_image(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns the (upper, lower) staff crops of a grandstaff image.

    The upper crop is the top two thirds of the image and the lower crop is
    the bottom two thirds, both full width.
    """
    height = image.shape[0]
    crop_height = int(height * OVERLAP_FRACTION)

    upper_image = image[0:crop_height, :]
    lower_image = image[height - crop_height : height, :]

    return upper_image, lower_image
