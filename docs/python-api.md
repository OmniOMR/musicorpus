# Python API

The `musicorpus` package reads a MusiCorpus dataset from python. It is meant for whoever *consumes* a dataset — training a model, computing statistics, converting to some other layout — rather than only for whoever builds one.

```python
from pathlib import Path

from musicorpus import Dataset

dataset = Dataset.load(Path("datasets/UFAL.OmniOMR"))

for page in dataset.split("train"):
    for staff in page.staves:
        musicxml = staff.transcription_path("musicxml")
        image = staff.image_path()
```


## Installing it

```bash
pip install 'musicorpus @ git+https://github.com/OmniOMR/musicorpus.git'
```

Everything on this page works from that, with **no dependencies installed at all** — see [what is parsed and what is not](#what-is-parsed-and-what-is-not) for why that is possible, and the [README](../README.md#installation) for the extras that the CLI commands need.


## What is parsed and what is not

The formats MusiCorpus itself defines are JSON, and the package parses them and hands back objects:

| File | Method | Type |
| --- | --- | --- |
| `musicorpus.json` | `dataset.manifest` | `MusicorpusManifest` |
| `splits.json` | `dataset.splits()` | `Splits` |
| `metadata.json` | `sample.metadata()` | `PageMetadata` |
| `layout.json` | `page.layout()` | `Layout` |
| `subdivisions.image.json` | `page.image_subdivisions()` | `ImageSubdivisions` |

Everything else is handed back as a `Path`, or `None` when the file is absent:

| File | Method |
| --- | --- |
| `image.jpg`, `image.{variant}.jpg` | `sample.image_path()` |
| `transcription.musicxml`, `.krn`, `.mung`, … | `sample.transcription_path(format)` |
| `coco-object-detection.json` | `sample.coco_path` |
| `mung-to-coco-ids-map.json` | `sample.mung_to_coco_map_path` |

That line is deliberate. MusicXML, MuNG, kern and the images belong to other libraries — mung, lmx, music21, OpenCV — and depending on any of them would make `pip install musicorpus` a heavy install for somebody who only wants to know which pages are in the training split. You get the path; you use whichever loader you already have.

```python
from mung.io import read_nodes_from_file  # your dependency, not ours

if (path := page.transcription_path("mung")) is not None:
    nodes = read_nodes_from_file(path)
```


## Datasets

`Dataset.load` opens a folder, checking that it holds a `musicorpus.json` — which is what distinguishes a MusiCorpus dataset from any other folder sitting in the same root.

```python
dataset = Dataset.load(Path("datasets/UFAL.OmniOMR"))
dataset.name  # "UFAL.OmniOMR", the folder name
dataset.manifest  # parsed musicorpus.json, read once and cached
dataset.readme_path  # Path | None
```

A root folder may hold several datasets, alongside folders that are not datasets at all:

```python
for dataset in Dataset.find_all(Path("datasets")):
    print(dataset.name, dataset.manifest.dataset_version)
```

`Dataset.load` raises `NotAMusicorpusDataset` for a folder without a manifest; `Dataset.is_dataset(path)` asks the same question without raising.


## Pages and splits

These are two different sets, and the specification says so: a splits file is *recommended* to cover every page but is not required to, and alternative splits files exist precisely so that pages can be left out.

```python
dataset.page_names  # every page folder on disk, sorted
dataset.pages()  # an iterator of Page over the same
dataset.page("some-page")  # by name, whether or not it exists

dataset.splits()  # parsed splits.json
dataset.split("train")  # an iterator of Page, in the file's order
```

The order a split lists its pages in is meaningful — the specification asks for it to be shuffled so that it can be trained on directly — so `split()` preserves it rather than sorting.

A page named by a split need not be on disk. Check when it matters:

```python
for page in dataset.split("train"):
    if not page.exists():
        continue
```

Alternative splits files are addressed by their variant name, so `splits.book-consistent.json` is:

```python
dataset.split_variants()  # ["book-consistent"]
dataset.splits("book-consistent")
dataset.split("train", "book-consistent")
```


## Samples: pages and subdivisions

A page and a subdivision of a page carry the same repertoire of files, so both are a `Sample` and anything reading images and transcriptions can take either.

```python
page = dataset.page("some-page")

page.staves  # list[Subdivision]
page.grandstaves
page.systems
page.subdivisions("Staves")  # the same, by folder name

staff = page.staves[0]
staff.name  # "2", or "6-7" for a grandstaff
staff.kind  # "Staves"
staff.page  # back to the Page
staff.page_name  # the page's name, also on a Page itself
```

Subdivisions come back sorted lexicographically by folder name, because the specification lets those names be any path-safe string — so `10` sorts before `2`. Sort them yourself if your dataset numbers them and you need numeric order.

Images and transcriptions:

```python
sample.image_path()  # image.jpg, or image.png / image.tif if that is what there is
sample.image_path("distorted")  # image.distorted.jpg
sample.image_path(suffix="png")  # only png
sample.image_variants()  # ["distorted", "synthetic"], not counting the default

sample.transcription_path("musicxml")  # Path | None
sample.transcription_formats()  # ["musicxml", "krn"] — what this sample actually has
```


## What is stable

The names re-exported from `musicorpus/__init__.py` are the public API:

`Dataset`, `Page`, `Subdivision`, `Sample`, `NotAMusicorpusDataset`, `MusicorpusManifest`, `Splits`, `Layout`, `PageMetadata`, `ImageSubdivisions`, `ErrorBag`, `CocoBbox`, `CocoDatasetMetadata`, `CocoImageMetadata`, `CocoLicense`, and the constants `SPECIFICATION_VERSION`, `SUBDIVISION_KINDS`, `TRANSCRIPTION_FORMATS`, `IMAGE_SUFFIXES`.

Import them from the package root:

```python
from musicorpus import Dataset, Splits
```

Everything below that — module layout, the `validation`, `statistics` and `exporters` subpackages — is internal arrangement and may move between versions. The exporters in particular are reference implementations rather than API.

`SPECIFICATION_VERSION` is the version of the *document* this package implements, which is not the version of the package and moves independently of it. A dataset declares which version it follows in its manifest:

```python
import musicorpus

if dataset.manifest.musicorpus_version != musicorpus.SPECIFICATION_VERSION:
    ...  # a dataset written against a different version of the specification
```


## A worked example

[`tests/data/TEST.Fixture`](../tests/data/TEST.Fixture) is a complete, tiny MusiCorpus dataset — four pages, two splits files, staves and grandstaves, an image variant, and pages with optional files missing. It is what the tests read, and it is small enough to inspect file by file when you are laying out a dataset of your own. [`tests/data/build_test_fixture.py`](../tests/data/build_test_fixture.py) builds it using this package's own writers.
