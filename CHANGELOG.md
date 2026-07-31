# Changelog

All notable changes to this repository are recorded here, in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) form.

Two things are versioned here and they move independently: the **MusiCorpus
specification**, which is the document in [spec/](spec/), and the
**`musicorpus` python package**, which is the code. Entries say which one they
concern. See [docs/versioning-and-releases.md](docs/versioning-and-releases.md).


## Unreleased

Nothing yet.


## 0.1.0 — 2026-07-31

The first release of the `musicorpus` package. The specification is unchanged
at 1.0 and is released separately, under its own tags.

Before this, the code was a folder of scripts run through a bash wrapper; it
could not be installed, imported, or depended upon. It now installs from the
repository URL, exposes a python API for reading a dataset, and carries a CLI
as a console script.

### Added

- A **python API for reading a dataset**: `Dataset.load(path)`, with `Page`,
  `Subdivision` and the `Sample` they share. It parses the JSON formats
  MusiCorpus defines — manifest, splits, layout, page metadata, image
  subdivisions — and hands back a `Path` for MusicXML, MuNG, kern and images,
  which belong to other libraries. `musicorpus/__init__.py` is the public
  surface; see [docs/python-api.md](docs/python-api.md).
- `Layout.load_from_file` and `Layout.parse_from_json`. `layout.json` could be
  written but not read, so nothing could consume one.
- `musicorpus --version`.
- Two fixture datasets under `tests/data/`, generated and committed: a
  conformant one the validator reports nothing on, and one that bends the
  rules on purpose. Both double as worked examples of the layout.
- A CI workflow running ruff, mypy and the tests on python 3.10 and 3.12, plus
  a job that opens the built wheel to check its data files and entry point.

### Changed

- **The package is installable.** The code moved from `app/` to
  `src/musicorpus/` with a `pyproject.toml`, replacing the `./musicorpus` bash
  wrapper and `requirements.txt`. Install it from the repository URL; the CLI
  becomes a console script. Requires python 3.10 or newer.
- **The base install declares no dependencies.** Reading a dataset is pure
  standard library. mung, pycocotools, lmx, music21, OpenCV and the rest moved
  behind the `validation`, `statistics` and `exporters` extras, and running a
  command without its extra reports which one to install. `opencv-python`
  became `opencv-python-headless`.
- **Exporters are grouped under one command**: `musicorpus export omniomr`
  rather than `musicorpus export-omniomr`, so that the commands a dataset
  consumer needs stay visible at the top level.
- **CLI flags are kebab-case**: `--page-names`, `--extend-splits`,
  `--n-attempts`, `--book-consistent`, `--ms-documents`, `--ms-editions`,
  `--ignore-splits-validation`.
- `musicorpus --help` answers in about four hundredths of a second rather than
  four tenths, because no command imports its dependencies until it runs.
- Module names are snake_case, and `coco_bbox.py` became `coco.py`, which now
  also holds the COCO metadata classes that used to sit in `mung_to_coco.py`.
- The specification moved to `spec/`, rendered by `spec/build.py`.

### Fixed

- **A manifest written by this package could not be read back on python
  3.10.** `created_at` is written with the `Z` designator the specification
  uses, and `datetime.fromisoformat` only accepted that from python 3.11
  onwards, so `musicorpus validate` raised `Invalid isoformat string` on every
  conformant dataset.
- **CLI error paths exited 0**, reporting failure as success to the shell.
- **The validators caught `KeyboardInterrupt`**, recording a Ctrl-C as a defect
  in whichever file was being read and carrying on to the next one.
- `CocoBbox` compares and hashes by value, rather than by identity.
- `mung2mxl_staff_index` was a closure over a loop variable.
