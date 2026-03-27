from pathlib import Path
import cv2


def get_image_size(image_path: str | Path) -> tuple[int, int]:
    """Returns image size as (width, height)"""
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR_BGR)
    assert img is not None
    height, width, channels = img.shape
    return width, height
