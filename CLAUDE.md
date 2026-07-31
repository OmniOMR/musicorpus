# MusiCorpus

This repository holds two things that are released separately:

- **The MusiCorpus specification** — [spec/musicorpus-specification.md](spec/musicorpus-specification.md), a set of guidelines for how an OMR dataset is laid out on disk. Version 1.0, released. This is the flagship artifact; the code exists to serve it.
- **The `musicorpus` python package** — `src/musicorpus/`, a CLI and a python API for building and consuming datasets in that format. Not yet released.

Keeping them in one repository is deliberate: the validator and the clauses it enforces stay honest by sitting next to each other. What it costs is a shared tag namespace, which is why `pyproject.toml` says which tags belong to the code — see [docs/versioning-and-releases.md](docs/versioning-and-releases.md) for the three version numbers involved and how not to confuse them. **Do not remove the `git_describe_command` override**: without it, tagging a new version of the document silently becomes the version of the code.

The folder structure is documented in [docs/repository-layout.md](docs/repository-layout.md), the public API in [docs/python-api.md](docs/python-api.md).


## Toolchain

The development environment is `.venv`, created with **python 3.10** — the floor of `requires-python`, so that syntax needing something newer fails here rather than in CI. Install with `.venv/bin/pip install -e '.[dev]'`. Everything runs out of it:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
```

The formatter owns the layout of the code — do not hand-wrap around it, and do not argue with it in review. Its one-time application across the codebase is commit `5d954e3`, listed in [.git-blame-ignore-revs](.git-blame-ignore-revs). Note that it also reformats python inside markdown fences and inside `tests/data/build_test_fixture.py`, whose templates generate the fixtures — regenerate those *after* formatting, not before.

mypy is not `strict`, and has no pinned `python_version` so that it checks against whichever interpreter runs it. mung, pycocotools, music21, converter21 and cv2 ship no type information, so strict mode would report hundreds of errors that say nothing about correctness. The configuration in `pyproject.toml` is the contract; tighten it as annotations arrive rather than adding `# type: ignore`.


## Three things that are easy to break

**The base install has no dependencies, and that is a promise.** The modules describing the format are standard library only, so `pip install musicorpus` cannot conflict with a consumer's environment; mung, pycocotools, lmx, music21 and OpenCV sit behind the `validation`, `statistics` and `exporters` extras. `tests/test_dependencies.py` imports each format module in a fresh interpreter and fails if it reached one of them — so adding `import mung` to `layout.py` breaks the build rather than breaking somebody's installation. Commands defer their imports into `execute` and wrap them in `cli/extras.py:requires`, which reports a missing extra as the command that installs it.

**Anything an installed package reads must be found relative to `__file__`** (package data) **or to the working directory** (generated files) — never relative to the repository root, which does not exist once the package is installed from a git URL.

**Two `file_name` conventions.** The specification states them in sections far apart and they are easy to confuse: `metadata.json`'s `file_name` is relative to the **root** folder and so begins with the dataset folder name, while COCO's `images[].file_name` in `layout.json` and `coco-object-detection.json` is relative to the **dataset** folder and does not.


## The exporters

`exporters/` holds **reference implementations, not product.** They are coupled to input data nobody outside the project has, and they are what a new dataset author reads before writing their own. `exporters/grandstaff/` is the small legible example; `exporters/omniomr/` is the real one. They are not part of the public API, are not covered by whatever the package version promises, and have no tests because there is nothing to run them against.


## Markdown conventions

Match the repository's existing markdown style when creating or editing `.md` files:

- Leave exactly one blank line after a heading.
- Leave exactly two blank lines before a heading (unless the heading is the first line of the file).
- Do not hard-wrap paragraphs — write each paragraph as a single line and let the editor soft-wrap it.
