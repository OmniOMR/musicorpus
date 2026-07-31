# MusiCorpus

This repository holds two things that are released separately:

- **The MusiCorpus specification** — [docs/musicorpus-specification/musicorpus-specification.md](docs/musicorpus-specification/musicorpus-specification.md), a set of guidelines for how an OMR dataset is laid out on disk. Version 1.0, released, tagged `specification`. This is the flagship artifact; the code exists to serve it.
- **The `musicorpus` python package** — `src/musicorpus/`, a CLI and a python API for building and consuming datasets in that format. Not yet released, versioned separately from the specification.

Keeping them in one repository is deliberate: the validator and the clauses it enforces stay honest by sitting next to each other. What that costs is a shared tag namespace, which is why the version configuration in `pyproject.toml` says which tags belong to the code.


## Three version numbers, easily confused

| Number | What it versions | Where it lives |
| --- | --- | --- |
| **The specification version** | The document. `1.0` today. | Its title, and the `specification` git tag. |
| **The package version** | The code: the CLI and the python API. Derived from the git tags, never written down. | Nowhere — computed at build time from `git describe --match 'v[0-9]*'`. |
| **`musicorpus_version`** | Which specification version a *dataset* claims to follow. | The `musicorpus.json` manifest inside each dataset. |

A `specification-1.1` tag must never be read as the version of the code, which is what the `git_describe_command` override in `pyproject.toml` prevents. Do not remove it.


## Toolchain

The development environment is `.venv`, created with **python 3.10** — the floor of `requires-python`, so that syntax needing something newer fails here rather than in CI. Install with `.venv/bin/pip install -e '.[dev]'`. Everything runs out of it:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy
```

`ruff format` is deliberately **not** part of the toolchain. This codebase has a hand-maintained wrapping style — arguments one per line, `+`-concatenated message strings — that the formatter would rewrite wholesale across 5000 lines. Match the surrounding style instead.

mypy is not `strict`. mung, pycocotools, music21, converter21 and cv2 ship no type information, so strict mode would report hundreds of errors that say nothing about correctness. The configuration in `pyproject.toml` is the contract; tighten it as annotations arrive rather than adding `# type: ignore`.


## Layout

```
src/musicorpus/
  cli/               one module per subcommand, plus run.py which registers them
  validation/        checks a dataset against the specification
  statistics/        aggregates dataset statistics
  exporters/         one subpackage per dataset that gets exported into the format
  *.py               the file formats themselves: manifest, splits, layout, metadata
```

**The exporters are reference implementations, not product.** They are coupled to input data nobody outside the project has, and they are what a new dataset author reads before writing their own. `exporters/grandstaff/` is the small legible example; `exporters/omniomr/` is the real one. They are not part of the public API and are not covered by whatever the package version promises.

Anything an installed package reads must be found relative to `__file__` (package data) or to the working directory (generated files) — never relative to the repository root, which does not exist once the package is installed from a git URL.


## Markdown conventions

Match the repository's existing markdown style when creating or editing `.md` files:

- Leave exactly one blank line after a heading.
- Leave exactly two blank lines before a heading (unless the heading is the first line of the file).
- Do not hard-wrap paragraphs — write each paragraph as a single line and let the editor soft-wrap it.
