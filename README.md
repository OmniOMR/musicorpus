# MusiCorpus dataset format

MusiCorpus is a set of guidelines for structuring an OMR dataset. This repository houses the format specificifation (the documentation) and a python CLI `./musicorpus` that provides tools for working with MusiCorpus datasets.


## Documentation

- [MusiCorpus Specification 1.0](docs/musicorpus-specification/musicorpus-specification.md)
- CLI commands
    - [Exporting OmniOMR Dataset to MusiCorpus](docs/exporting-omniomr-dataset.md)
    - [Computing OmniOMR Splits](docs/computing-omniomr-splits.md)


## CLI

To use the CLI, simply clone this repo, set up the python virtual environment and then you should be able to use the `./musicorpus` CLI:

```bash
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
```

Now use the CLI:

```bash
./musicorpus --help
```

These are the commands available in the CLI:

- `./musicorpus` **`validate`** `--help`: To be added...
- `./musicorpus` **`inspect`** `--help`: To be added...
- `./musicorpus` **`statistics`** `--help`: To be added...
- `./musicorpus` **`export-omniomr`** `--help`: Used to build the OmniOMR dataset from its sources into the MusiCorpus structure. See [Exporting OmniOMR Dataset to MusiCorpus](docs/exporting-omniomr-dataset.md) for more.
- `./musicorpus` **`omniomr-splits`** `--help`: Utility for defining the `splits.json` files for the OmniOMR dataset. See [Computing OmniOMR Splits](docs/computing-omniomr-splits.md) for more.
