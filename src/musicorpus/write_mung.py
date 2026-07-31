from mung.graph import NotationGraph
from mung.io import write_nodes_to_string
from pathlib import Path


def write_mung(
        mung_graph: NotationGraph,
        file_path: Path,
        document: str,
        dataset: str
):
    """Writes MuNG graph to a file. Patches the mung.io.write_nodes_to_file
    function, which does not store the file as UTF-8 on windows by default.
    This function correctes that and enforces UTF-8 always."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    output = write_nodes_to_string(mung_graph.vertices, document, dataset)
    with open(file_path, mode="w", encoding="utf-8") as output_file:

        # replace occurrences of "& " with "&amp; " because the mung package
        # does not escape entities and it would fail when tryin to load xml
        # (this is a hacky fix, instead the mung package should be fixed)
        # https://github.com/OmniOMR/mung/issues/15
        output.replace("& ", "&amp; ")

        output_file.write(output)
