"""The base install must stay free of third-party dependencies.

`pip install musicorpus` declares no dependencies at all, so that anybody
consuming a dataset can read its manifest, splits, layout and metadata without
pulling in mung, OpenCV or music21. That promise is only as good as the import
graph underneath it, which is what this file checks: it does not need those
packages to be absent, only for the modules in question not to reach them.
"""

import subprocess
import sys

import pytest

# The modules that describe the format itself — what the base install is for.
FORMAT_MODULES = [
    "musicorpus",
    "musicorpus.coco",
    "musicorpus.dataset",
    "musicorpus.error_bag",
    "musicorpus.hidden_prints",
    "musicorpus.image_subdivisions",
    "musicorpus.layout",
    "musicorpus.manifest",
    "musicorpus.page_metadata",
    "musicorpus.read_page_names",
    "musicorpus.splits",
]

OPTIONAL_PACKAGES = [
    "converter21",
    "cv2",
    "imagesize",
    "lmx",
    "mung",
    "music21",
    "numpy",
    "pycocotools",
    "requests",
    "tqdm",
    "yaml",
]


@pytest.mark.parametrize("module", FORMAT_MODULES)
def test_format_module_imports_nothing_optional(module: str) -> None:
    """Importing it in a fresh interpreter must not reach an extra."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys\nimport {module}\n"
            f"print(','.join(m for m in {OPTIONAL_PACKAGES!r} if m in sys.modules))\n",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"importing {module} pulled in: {result.stdout.strip()} — "
        "the base install declares no dependencies, so this would be an "
        "ImportError for anyone who installed musicorpus without extras"
    )
