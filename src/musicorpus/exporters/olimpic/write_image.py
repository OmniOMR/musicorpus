"""Decides how an exported image is written to disk."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class ImageOutput:
    """The image-writing options chosen for one export run."""

    jpeg_quality: int
    """Quality of the written `image.jpg` files, 1 to 100.

    The default the CLI passes is low on purpose — see `DEFAULT_JPEG_QUALITY`
    in `cli/export_olimpic_command.py`, which is where it is chosen, because
    the parser has to state it without importing OpenCV to do so.
    """

    write_png: bool = False
    """Whether to write a lossless `image.png` beside each `image.jpg`.

    The specification requires the JPEG and permits the PNG alongside it, so
    this is how an export keeps the source pixels intact for a use case that
    needs them — at the price of carrying both encodings.
    """

    def write(self, folder: Path, image: np.ndarray, png_source: Path | None = None) -> None:
        """Writes `image.jpg`, and `image.png` when asked for.

        `png_source` is the file the image was decoded from, when it is the
        whole image rather than a crop of it. Copying that file beats
        re-encoding the array: the bytes stay exactly as OLiMPiC published
        them, and no encoder setting can quietly change them.
        """
        cv2.imwrite(str(folder / "image.jpg"), image, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])

        if not self.write_png:
            return

        if png_source is not None:
            shutil.copy(png_source, folder / "image.png")
        else:
            cv2.imwrite(str(folder / "image.png"), image)
