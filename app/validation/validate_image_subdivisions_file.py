from pathlib import Path
from ..ErrorBag import ErrorBag
from ..ImageSubdivisions import ImageSubdivisions
import traceback
from ..get_image_size import get_image_size
from ..CocoBbox import CocoBbox


def validate_image_subdivisions_file(
        dataset_path: Path,
        image_subdivisions_file: Path,
        errors: ErrorBag
):
    relative_path = image_subdivisions_file.relative_to(dataset_path)
    page_name = relative_path.parts[0]

    # load the subdivisions file
    try:
        subdivisions = ImageSubdivisions.load_from(image_subdivisions_file)
    except:
        errors.add_error(
            page_name=page_name,
            message=f"The file {image_subdivisions_file} cannot be loaded:\n" +
                traceback.format_exc()
        )
        return

    # get the size of the page-level image
    page_width, page_height = get_image_size(
        image_subdivisions_file.parent / "image.jpg"
    )
    page_bbox = CocoBbox(0, 0, page_width, page_height)

    # === run assertions ===

    for subdivision_message, subdivision_dict, subdivision_folder in [
        ("staff", subdivisions.staves, "Staves"),
        ("grandstaff", subdivisions.grandstaves, "Grandstaves"),
        ("system", subdivisions.systems, "Systems"),
    ]:
        for name, bbox in subdivision_dict.items():
            
            # check that the subdivision bbox is contained in the page
            if bbox.area != bbox.intersect_with(page_bbox).area:
                errors.add_error(
                    page_name=page_name,
                    message=f"In subdivisions.image.json, the " +
                    f"{subdivision_message} {name} {repr(bbox)} is not contained " +
                    f"within the page boundaries {repr(page_bbox)}."
                )
            
            # check that the subdivision bbox size matches the subdivision image size
            sub_width, sub_height = get_image_size(
                image_subdivisions_file.parent / subdivision_folder / name / "image.jpg"
            )
            if sub_width != bbox.width or sub_height != bbox.height:
                errors.add_error(
                    page_name=page_name,
                    message=f"In subdivisions.image.json, the " +
                    f"{subdivision_message} {name} bbox size {repr(bbox)} does not match " +
                    f"the subdivision image size ({sub_width}, {sub_height})."
                )
