import tqdm
from pathlib import Path
from ..ImageSubdivisions import ImageSubdivisions
from ..ErrorBag import ErrorBag
import cv2


def subdivide_images(
        page_names: list[str],
        output_folder: Path,
        errors: ErrorBag
):
    """Crops page images into all of their subdivisions"""
    for page_name in tqdm.tqdm(page_names, "Subdividing images"):
        
        # load subdivisions cropboxes
        subdivisions_path = output_folder / page_name / "subdivisions.image.json"
        if not subdivisions_path.exists():
            errors.add_error(
                page_name,
                "subdivisions.image.json not found in: " + str(subdivisions_path)
            )
            continue
        subdivisions = ImageSubdivisions.load_from(subdivisions_path)

        # load page image
        image_path = output_folder / page_name / "image.jpg"
        if not image_path.exists():
            errors.add_error(
                page_name,
                "Page-level image.jpg not found in: " + str(image_path)
            )
            continue
        page_image = cv2.imread(str(image_path), cv2.IMREAD_COLOR_BGR)
        assert page_image is not None

        # staves
        for staff_name, bbox in subdivisions.staves.items():
            cv2.imwrite(
                str(output_folder / page_name / "Staves" / staff_name / "image.jpg"),
                page_image[
                    bbox.top:bbox.bottom,
                    bbox.left:bbox.right,
                    :
                ]
            )
        
        # grandstaves
        for grandstaff_name, bbox in subdivisions.grandstaves.items():
            cv2.imwrite(
                str(output_folder / page_name / "Grandstaves" / grandstaff_name / "image.jpg"),
                page_image[
                    bbox.top:bbox.bottom,
                    bbox.left:bbox.right,
                    :
                ]
            )

        # systems
        for system_name, bbox in subdivisions.systems.items():
            cv2.imwrite(
                str(output_folder / page_name / "Systems" / system_name / "image.jpg"),
                page_image[
                    bbox.top:bbox.bottom,
                    bbox.left:bbox.right,
                    :
                ]
            )