# MusiCorpus dataset format

MusiCorpus is a set of guidelines for structuring an OMR dataset. This repository houses the format specificifation (the documentation) and a python CLI `./musicorpus` that provides tools for working with MusiCorpus datasets.


## Documentation

- [MusiCorpus Specification 1.0](docs/musicorpus-specification/musicorpus-specification.md)


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
