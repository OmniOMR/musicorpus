# MusiCorpus dataset format

MusiCorpus is a set of guidelines for structuring an OMR dataset. This repository houses the format specificifation (the documentation) and the `musicorpus` python package, which provides tools for working with MusiCorpus datasets.


## Datasets

This is a list of datasets that follow the MusiCorpus format:

- `pending` **MUSCIMA++ 3.0**
- `2026-08-03` **OLiMPiC 1.0** ([build yourself](docs/exporting-olimpic-dataset.md)), contains additional staff-level subdivisions.
- `2026-04-30` **MusiCorpus 1.0** ([download](http://hdl.handle.net/20.500.12800/1-6147), [arxiv](https://arxiv.org/abs/2605.18436)), contains [**Dolores 1.0**](https://pages.cvc.uab.es/musicscores/loladocs/index.html) and [**OmniOMR 1.0**](https://ufal.mff.cuni.cz/grants/omniomr) datasets.


## Documentation

- [**MusiCorpus Specification 1.0**](spec/musicorpus-specification.md) — the format itself
- [Python API](docs/python-api.md) — reading a dataset from python
- [Repository layout](docs/repository-layout.md) — what is where, and why
- [Versioning and releases](docs/versioning-and-releases.md) — the specification and the package are released separately
- [Changelog](CHANGELOG.md)
- CLI commands
    - [Exporting OmniOMR Dataset to MusiCorpus](docs/exporting-omniomr-dataset.md)
    - [Computing OmniOMR Splits](docs/computing-omniomr-splits.md)
    - [Exporting OLiMPiC Dataset to MusiCorpus](docs/exporting-olimpic-dataset.md)


## Python API

Reading a dataset needs no dependencies and no CLI:

```python
from pathlib import Path

from musicorpus import Dataset

dataset = Dataset.load(Path("datasets/UFAL.OmniOMR"))

for page in dataset.split("train"):
    for staff in page.staves:
        musicxml = staff.transcription_path("musicxml")
        image = staff.image_path()
```

See [Python API](docs/python-api.md) for the whole surface.


## Installation

The package requires **python 3.10 or newer** and is installed from this repository:

```bash
pip install 'musicorpus @ git+https://github.com/OmniOMR/musicorpus.git'
```

That base install has **no dependencies at all**. Reading a MusiCorpus dataset — its manifest, splits, layout, page metadata, subdivisions and COCO boxes — is pure standard library, so consuming a dataset cannot conflict with anything already in your environment.

The heavier machinery lives in extras, so you install only what you use:

| Extra | Installs | Needed for |
| --- | --- | --- |
| *(none)* | nothing | reading the format from python |
| `validation` | mung, pycocotools, lmx, imagesize, tqdm | `musicorpus validate` |
| `statistics` | pyyaml, imagesize, tqdm | `musicorpus statistics` |
| `exporters` | the above plus music21, converter21, OpenCV, numpy, requests | `musicorpus export ...` |
| `all` | everything | |

```bash
pip install 'musicorpus[validation] @ git+https://github.com/OmniOMR/musicorpus.git'
```

Running a command whose extra is missing tells you which one to install rather than raising an `ImportError`.

To work on the package, clone the repository and install it in editable form:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```


## CLI

Installing the package puts a `musicorpus` command on the path:

```bash
musicorpus --help
```

These are the commands available in the CLI:

- `musicorpus` **`validate`** `--help`: Validates that the given dataset conforms to the MusiCorpus structure and produces a list of errors if not.
- `musicorpus` **`inspect`** `--help`: To be added...
- `musicorpus` **`statistics`** `--help`: Aggregates dataset statistics across splits, subdivisions, and transcription file formats.
- `musicorpus` **`export`** `--help`: Builds a specific dataset from its own sources into the MusiCorpus structure. One exporter per dataset:
    - `musicorpus export` **`grandstaff`** `--help`: To be added...
    - `musicorpus export` **`olimpic`** `--help`: See [Exporting OLiMPiC Dataset to MusiCorpus](docs/exporting-olimpic-dataset.md) for more.
    - `musicorpus export` **`omniomr`** `--help`: See [Exporting OmniOMR Dataset to MusiCorpus](docs/exporting-omniomr-dataset.md) for more.
- `musicorpus` **`omniomr-splits`** `--help`: Utility for defining the `splits.json` files for the OmniOMR dataset. See [Computing OmniOMR Splits](docs/computing-omniomr-splits.md) for more.

The exporters are reference implementations rather than tools most users need. If you are bringing a dataset of your own into the format, they are the worked examples to read — and a new one is welcome as a pull request.
