# Exporting OLiMPiC Dataset to MusiCorpus

OLiMPiC is distributed as two datasets — *scanned* and *synthetic* — that hold the same music with different images and span a slightly different set of pages. They are exported separately and become two MusiCorpus datasets, `UFAL.OlimpicScanned` and `UFAL.OlimpicSynthetic`, because a MusiCorpus dataset is one folder with one `musicorpus.json` and these two differ in what they are.

Unlike the OmniOMR export, this one needs nothing but the published archives: no cluster access, no Google Drive, no spreadsheets. Everything the export needs is inside the `.tar.gz` files.


## 1. Download the archives

Both come from the [OLiMPiC datasets release](https://github.com/ufal/olimpic-icdar24/releases/tag/datasets). I keep them in `~/datasets`; adjust as you wish.

```bash
cd ~/datasets

BASE="https://github.com/ufal/olimpic-icdar24/releases/download/datasets"
wget "$BASE/olimpic-1.0-scanned.2024-02-12.tar.gz"
wget "$BASE/olimpic-1.0-synthetic.2024-02-12.tar.gz"
```

> **Note:** The same data is also published at [LINDAT](https://hdl.handle.net/11234/1-5419), which is the citable landing page for the dataset. Use it if a GitHub asset refuses to download.


## 2. Untar them

Each archive contains a single top-level folder, so this lands them side by side in `~/datasets`:

```bash
tar -xzf olimpic-1.0-scanned.2024-02-12.tar.gz
tar -xzf olimpic-1.0-synthetic.2024-02-12.tar.gz
```

You should end up with `~/datasets/olimpic-1.0-scanned` and `~/datasets/olimpic-1.0-synthetic`, each holding a `samples/` folder, the `samples.*.txt` splits files, a `README.md` and a `LICENSE`. Those folders are what the export reads.


## 3. Run the export

The two runs differ in three options that must agree with each other: `--olimpic` says which archive is being read, `--variant` picks the `musicorpus.json` and `README.md` written into the output, and `--output` names the folder. Getting `--variant` wrong is caught before any work is done, because the output folder name has to match it.

**Scanned:**

```bash
musicorpus export olimpic \
  --olimpic ~/datasets/olimpic-1.0-scanned \
  --variant scanned \
  --output ~/datasets/UFAL.OlimpicScanned
```

**Synthetic:**

```bash
musicorpus export olimpic \
  --olimpic ~/datasets/olimpic-1.0-synthetic \
  --variant synthetic \
  --output ~/datasets/UFAL.OlimpicSynthetic
```

Add `--force` to overwrite an output folder that already exists. Add `--skip-specification-pdf` to export without a network connection — the specification PDF is otherwise downloaded from its release and written into the dataset root, and `musicorpus validate` expects to find it.

The synthetic export is the long one: it is roughly six times the samples of the scanned one, and every sample is an image decode, two crops and a re-encode.


### Image quality and size

MusiCorpus requires the image to be published as JPEG. OLiMPiC ships PNG, and these images are the best case for PNG and the worst for JPEG — grayscale, near-bilevel, mostly white paper — so a faithful re-encoding balloons the dataset. At OpenCV's default quality of 95 the scanned export is 3.4 GB out of a 336 MB archive, and the synthetic one would be several times that.

So the export compresses hard by default, `--jpeg-quality 20`, which is chosen to land near the size of the source archive:

| Quality | Scanned | Synthetic |
| --- | --- | --- |
| 95 (OpenCV's default) | 6.9× the source PNGs | 2.8× |
| 40 | 2.9× | 1.4× |
| **20 (the default here)** | **2.1×** | **1.1×** |
| 10 | 1.6× | 0.8× |

Synthetic reaches parity; scanned cannot, because JPEG does poorly on scanner noise — even quality 5 is still 1.3× there. At quality 20 there is visible ringing around staff lines and note heads when you zoom to 1:1, and every symbol stays unambiguous. Since this data exists to train recognition models, that is closer to a mild augmentation than to damage.

Two ways out when a use case needs the pixels:

```bash
# a gentler JPEG
musicorpus export olimpic ... --jpeg-quality 90

# or keep the originals losslessly beside the JPEGs
musicorpus export olimpic ... --png
```

`--png` writes an `image.png` next to every `image.jpg`, which the specification permits alongside the mandatory JPEG. For a grandstaff that PNG is the OLiMPiC file copied byte for byte rather than re-encoded; for a staff it is the lossless crop. The dataset then carries both encodings and grows accordingly.

Before releasing an export, check that `src/musicorpus/exporters/olimpic/assets/` holds the values you want — `musicorpus.{variant}.json` and `README.{variant}.md` are copied into the dataset as they stand.


## 4. Validate the result

```bash
musicorpus validate \
  --dataset ~/datasets/UFAL.OlimpicScanned \
  --output ~/datasets/olimpic-scanned-errors.txt
```

A clean export reports `Perfect dataset with no errors!` and writes no error file.


## What the export produces

OLiMPiC is a grandstaff-level dataset: each sample is one system of one page of one score, as an image crop and a MusicXML transcription. The pages those crops came from are not part of the distribution, so the export produces **page folders that contain no files of their own** — only subdivisions. This is the shape the specification sketches in its Example 3.

```
UFAL.OlimpicScanned/ 📚
├── musicorpus.json 🏛️
├── musicorpus-specification.pdf
├── README.md
├── LICENSE.txt
├── splits.json 🪓
│
└── 5026306-p5/ 📜
    ├── Grandstaves/ 🎼
    │   ├── 1/
    │   │   ├── image.jpg 🖼️
    │   │   └── transcription.musicxml 📄
    │   └── 2/
    └── Staves/ 🎼
        ├── 1a/, 1b/
        └── 2a/, 2b/
```

**Page names** are `{score}-p{page}`, out of OLiMPiC's `samples/{score}/p{page}-s{system}`. **Grandstaves** are named by the system number within the page, rather than by the staff numbers the specification recommends (`1-2`, `3-4`), because OLiMPiC's processing of the OpenScore Lieder corpus did not preserve the page's staff numbering. **Staves** carry the name of their grandstaff with an `a` or `b` suffix for the upper and lower staff.

The `Staves` subdivision does not exist in OLiMPiC and is derived by the export:

- The transcription is separated with `lmx`, which refuses when a voice crosses between the two staves. About one grandstaff in six is such a case and is left without staves, so `Staves` covers less of the dataset than `Grandstaves` does. The counts are printed when the export finishes.
- The image is cut into the upper two thirds and the lower two thirds of the grandstaff crop, so the two overlap in the middle third. OLiMPiC carries no staff coordinates to cut against, and a cut down the middle would slice off stems, beams and ledger lines. A staff image therefore *contains* its staff rather than being a tight crop of it.

`splits.json` follows the OLiMPiC splits, with `dev` renamed to `validation`. The scanned variant ships no training data, so its `train` split is written as an empty list. This page-level mapping only works because no OLiMPiC page has its systems spread across two splits — the export checks the resulting splits against the folders it wrote and reports a mismatch.
