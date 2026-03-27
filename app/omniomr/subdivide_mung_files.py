import tqdm
from pathlib import Path
from ..ImageSubdivisions import ImageSubdivisions
from ..ErrorBag import ErrorBag
from ..crop_mung import crop_mung
from ..write_mung import write_mung
from mung.graph import NotationGraph
from mung.io import read_nodes_from_file


def subdivide_mung_files(
        page_names: list[str],
        output_folder: Path,
        errors: ErrorBag,
        mung_dataset_name: str
):
    """Crops page MuNG files into all of their subdivisions"""
    for page_name in tqdm.tqdm(page_names, "Subdividing MuNG files"):
        
        # load subdivisions cropboxes
        subdivisions_path = output_folder / page_name / "subdivisions.image.json"
        if not subdivisions_path.exists():
            errors.add_error(
                page_name,
                "subdivisions.image.json not found in: " + str(subdivisions_path)
            )
            continue
        subdivisions = ImageSubdivisions.load_from(subdivisions_path)

        # load page mung
        mung_path = output_folder / page_name / "transcription.mung"
        if not mung_path.exists():
            errors.add_error(
                page_name,
                "Page-level transcription.mung not found in: " + str(mung_path)
            )
            continue
        mung_graph = NotationGraph(read_nodes_from_file(mung_path))

        # staves
        for staff_name, bbox in subdivisions.staves.items():
            write_mung(
                crop_mung(mung_graph, bbox),
                output_folder / page_name / "Staves" / staff_name / "transcription.mung",
                document=f"{page_name}_Staves_{staff_name}",
                dataset=mung_dataset_name
            )
        
        # grandstaves
        for grandstaff_name, bbox in subdivisions.grandstaves.items():
            write_mung(
                crop_mung(mung_graph, bbox),
                output_folder / page_name / "Grandstaves" / grandstaff_name / "transcription.mung",
                document=f"{page_name}_Grandstaves_{grandstaff_name}",
                dataset=mung_dataset_name
            )

        # systems
        for system_name, bbox in subdivisions.systems.items():
            write_mung(
                crop_mung(mung_graph, bbox),
                output_folder / page_name / "Systems" / system_name / "transcription.mung",
                document=f"{page_name}_Systems_{system_name}",
                dataset=mung_dataset_name
            )
