from pathlib import Path
import shutil
import json
import xml.etree.ElementTree as ET
from .musescore_to_mxl_conversion import musescore_to_mxl_conversion
from .get_image_path import get_image_path
from .load_musicxml_string import load_musicxml_string
from .slice_musicxml_to_systems import slice_musicxml_to_systems
from .slice_mung_to_systems import slice_mung_to_systems
from .export_graph_to_coco import COCORecord, COCOExporter
from .process_metadata_csv import prepare_metadata_per_page, find_best_random_split, output_split_to_json
from mung.graph import NotationGraph, Node
from mung.io import read_nodes_from_file, write_nodes_to_string
import cv2


def perform_dataset_export(
        page_names: list[str],
        mung_studio_folder: Path,
        editions_folder: Path,
        metadata: list[dict[str, str]],
        output_folder: Path,
):
    """Run the dataset export process (builds the dataset from our soruces)"""
    
    # convert MSCZ to MusicXML via MuseScore
    musescore_to_mxl_conversion(
        [
            editions_folder / (page_name + ".mscz")
            for page_name in page_names
        ],
        target_format=".musicxml",
        replace_existing_files=True
    )

    # create the output folder
    output_folder.mkdir(parents=True)

    # prepare metadata mapping from page name to metadata dict for page-wise export
    # metadata_per_page = prepare_metadata_per_page(
    #     metadata=metadata,
    #     page_names=page_names
    # )

    # Run optimally stratified split finding (brute-force, takes a few minutes for 100 pages with 10^6 iterations)
    # N_RANDOM_SPLITS = 10000  # 10^4 for testing, but use 10^6 samples for live run. It takes approx. 5 mins on M2 CPU.
    # SPLIT_FILE = output_folder / "dataset_splits.json"
    # STRICT_SPLIT_FILE = output_folder / "dataset_splits_STRICT.json"
    # best_split, best_stratification = find_best_random_split(metadata_per_page,
    #                                                          page_names,
    #                                                          allow_book_overlap=True,  # Permissive: books can repeat across splits
    #                                                          n_splits=N_RANDOM_SPLITS)
    # strict_best_split, strict_best_stratification = find_best_random_split(metadata_per_page,
    #                                                                        page_names,
    #                                                                        allow_book_overlap=False,  # Strict
    #                                                                        n_splits=N_RANDOM_SPLITS)
    # output_split_to_json(best_split, SPLIT_FILE)
    # output_split_to_json(strict_best_split, STRICT_SPLIT_FILE)

    # run export per page
    for i, page_name in enumerate(page_names):
        print(f"{i+1}/{len(page_names)}", "Exporting", page_name, "...")
        output_document_folder = output_folder / page_name
        output_document_folder.mkdir()
        export_one_page(
            page_name=page_name,
            mung_studio_document_folder=mung_studio_folder / page_name,
            musicxml_path=editions_folder / (page_name + ".musicxml"),
            mscz_path=editions_folder / (page_name + ".mscz"),
            # metadata=metadata_per_page[page_name],
            output_document_folder=output_document_folder,
        )

    # COCO EXPORT

    coco_exporter = COCOExporter()
    # register whole images
    for i, folder in enumerate(output_folder.iterdir()):
        if folder.is_dir():
            name = folder.name
            print(f"{i + 1}/{len(page_names)}", "Creating COCO record", name, "...")
            mung_path = folder / "transcription.mung"
            assert mung_path.exists()
            image_path = get_image_path(folder)
            height, width = get_image_size(image_path)
            coco_exporter.register_record(COCORecord(
                name,
                image_path,
                mung_path,
                width,
                height,
            ))

            # register systems
            for system_folder in (folder / "Systems").iterdir():
                name = system_folder.name
                # print(f"  - Creating COCO record for System: {name}")
                mung_path = system_folder / "transcription.mung"
                assert mung_path.exists()
                image_path = get_image_path(system_folder)
                height, width = get_image_size(image_path)
                coco_exporter.register_record(COCORecord(
                    f"system-{name}-of-{folder.name}",
                    image_path,
                    mung_path,
                    width,
                    height,
                ))
    
    coco_exporter.export(output_folder / "coco-object-detection.json", indent=4)


def get_image_size(image_path: str | Path) -> tuple[int, int]:
    """
    Returns image `height, width`.
    """
    height, width, channels = cv2.imread(str(image_path), cv2.IMREAD_COLOR_BGR).shape
    return height, width


def write_nodes_to_file_utf8(nodes: list[Node], file_path: Path, document: str, dataset: str) -> None:
    """
    Force utf8 export. Installed mung library version does not support it.

    (Python saves uses UTF8 by default on Linux, but not on Windows.)
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    output = write_nodes_to_string(nodes, document, dataset)
    with open(file_path, mode="w", encoding="utf-8") as output_file:
        output_file.write(output)


def export_one_page(
        page_name: str,
        mung_studio_document_folder: Path,
        musicxml_path: Path,
        mscz_path: Path,
        # metadata: dict[str, str],
        output_document_folder: Path,
):
    # copy image
    source_image_path = get_image_path(mung_studio_document_folder, "image")
    image_suffix = source_image_path.suffix # .jpg or .png
    target_image_path = output_document_folder / ("image" + image_suffix)
    shutil.copy(source_image_path, target_image_path)
    page_image = cv2.imread(str(source_image_path), cv2.IMREAD_COLOR_BGR)

    # write metadata.json
    # with open(output_document_folder / "metadata.json", "w", encoding="utf-8") as f:
    #     json.dump(metadata, f, indent=4, ensure_ascii=False)

    # copy MuNG transcription
    shutil.copy(
        mung_studio_document_folder / "mung.xml",
        output_document_folder / "transcription.mung",
    )

    # load MuNG graph
    mung_graph = NotationGraph(read_nodes_from_file(
        mung_studio_document_folder / "mung.xml"
    ))

    # load MusicXML and write it as page-level transcription
    musicxml_string = load_musicxml_string(musicxml_path.with_suffix(""))
    musicxml_tree: ET.ElementTree = ET.ElementTree(ET.fromstring(musicxml_string))
    assert musicxml_tree.getroot().tag == "score-partwise"
    with open(output_document_folder / "transcription.musicxml", "w") as f:
        f.write(musicxml_string)

    # copy MuseScore transcription
    shutil.copy(mscz_path, output_document_folder / "transcription.mscz")

    # TODO: write segmentation.json

    # === System slices ===

    # write per-system MuNG slices
    mung_systems = slice_mung_to_systems(
        mung_graph,
        image_width=page_image.shape[1],
        image_height=page_image.shape[0],
    )
    for mung_system in mung_systems:
        path = output_document_folder / "Systems" \
            / str(mung_system.number) / "transcription.mung"
        write_nodes_to_file_utf8(
            mung_system.nodes,
            path,
            dataset=mung_graph.vertices[0].dataset,
            document=f"system-{mung_system.number}-of-" \
                + mung_graph.vertices[0].document,
        )

    # write per-system images
    for mung_system in mung_systems:
        system_image = page_image[
            mung_system.crop_bbox_trbl[0]:mung_system.crop_bbox_trbl[2],
            mung_system.crop_bbox_trbl[3]:mung_system.crop_bbox_trbl[1],
            :
        ]
        path = output_document_folder / "Systems" \
            / str(mung_system.number) / ("image" + image_suffix)
        cv2.imwrite(str(path), system_image)

    # write per-system musicxml slices
    musicxml_system_trees = slice_musicxml_to_systems(musicxml_tree)
    assert len(musicxml_system_trees) == len(mung_systems), \
        f"MuNG system count ({len(mung_systems)}) " + \
        f"and MusicXML ({len(musicxml_system_trees)}) system " + \
        "counts do not match"
    for i, musicxml_system_tree in enumerate(musicxml_system_trees):
        # TODO: check staff count to match between mung and musicxml
        path = output_document_folder / "Systems" \
            / str(i + 1) / "transcription.musicxml"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            musicxml_string = str(ET.tostring(
                musicxml_system_tree.getroot(),
                encoding="utf-8",
                xml_declaration=True
            ), "utf-8")
            f.write(musicxml_string)
