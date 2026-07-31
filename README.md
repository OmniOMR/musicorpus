# MusiCorpus dataset format

MusiCorpus is a set of guidelines for structuring an OMR dataset. This repository houses the format specificifation (the documentation) and the `musicorpus` python package, which provides tools for working with MusiCorpus datasets.


## Datasets

This is a list of datasets that follow the MusiCorpus format:

- `pending` **MUSCIMA++ 3.0**
- `2026-04-30` **MusiCorpus 1.0** ([download](http://hdl.handle.net/20.500.12800/1-6147)), contains [**Dolores 1.0**](https://pages.cvc.uab.es/musicscores/loladocs/index.html) and [**OmniOMR 1.0**](https://ufal.mff.cuni.cz/grants/omniomr) datasets.


## Documentation

- [MusiCorpus Specification 1.0](docs/musicorpus-specification/musicorpus-specification.md)
- CLI commands
    - [Exporting OmniOMR Dataset to MusiCorpus](docs/exporting-omniomr-dataset.md)
    - [Computing OmniOMR Splits](docs/computing-omniomr-splits.md)


## Installation

The package requires **python 3.10 or newer** and is installed from this repository:

```bash
pip install 'musicorpus @ git+https://github.com/OmniOMR/musicorpus.git'
```

To work on it, clone the repository and install it in editable form:

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
- `musicorpus` **`export-grandstaff`** `--help`: To be added...
- `musicorpus` **`export-omniomr`** `--help`: Used to build the OmniOMR dataset from its sources into the MusiCorpus structure. See [Exporting OmniOMR Dataset to MusiCorpus](docs/exporting-omniomr-dataset.md) for more.
- `musicorpus` **`omniomr-splits`** `--help`: Utility for defining the `splits.json` files for the OmniOMR dataset. See [Computing OmniOMR Splits](docs/computing-omniomr-splits.md) for more.
