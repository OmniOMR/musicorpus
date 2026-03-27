import tqdm
from pathlib import Path
from ..ImageSubdivisions import ImageSubdivisions
from ..ErrorBag import ErrorBag


def create_subdivisions_folders(
        page_names: list[str],
        output_folder: Path,
        errors: ErrorBag
):
    """Creates empty folders for all existing subdivisions for all pages"""
    for page_name in tqdm.tqdm(page_names, "Creating subdivisions folders"):
        
        # load subdivisions cropboxes
        source_path = output_folder / page_name / "subdivisions.image.json"
        if not source_path.exists():
            errors.add_error(
                page_name,
                "subdivisions.image.json not found in: " + str(source_path)
            )
            continue
        subdivisions = ImageSubdivisions.load_from(source_path)
        
        # staves
        for staff_name in subdivisions.staves.keys():
            (output_folder / page_name / "Staves" / staff_name).mkdir(parents=True)
        
        # grandstaves
        for grandstaff_name in subdivisions.grandstaves.keys():
            (output_folder / page_name / "Grandstaves" / grandstaff_name).mkdir(parents=True)

        # systems
        for system_name in subdivisions.systems.keys():
            (output_folder / page_name / "Systems" / system_name).mkdir(parents=True)
