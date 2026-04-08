from pathlib import Path
from ..ErrorBag import ErrorBag
from mung.io import read_nodes_from_file
from mung.graph import NotationGraph
import traceback


def validate_mung_file(
        dataset_path: Path,
        mung_file: Path,
        errors: ErrorBag
):
    relative_path = mung_file.relative_to(dataset_path)
    page_name = relative_path.parts[0]
    is_subdivision = len(relative_path.parts) > 2

    # load mung file
    try:
        mung_graph = NotationGraph(read_nodes_from_file(mung_file))
    except:
        errors.add_error(
            page_name=page_name,
            message=f"The file {mung_file} cannot be loaded:\n" +
                traceback.format_exc()
        )
        return

    # ... here more assertions can be performed ...
