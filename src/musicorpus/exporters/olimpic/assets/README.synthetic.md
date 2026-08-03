# OLiMPiC Synthetic Dataset

This is the synthetic variant of the OLiMPiC 1.0 dataset, repackaged into the [MusiCorpus](https://github.com/OmniOMR/musicorpus) format. It is intended for Optical Music Recognition (OMR) use cases, particularly end-to-end recognition of pianoform music. The original dataset is distributed at https://hdl.handle.net/11234/1-5419 and its accompanying code lives at https://github.com/ufal/olimpic-icdar24.

OLiMPiC is a processed subset of the [OpenScore Lieder](https://github.com/OpenScore/Lieder) corpus, narrowed to the piano parts of the songs. It is annotated at the grandstaff level: each sample is one grandstaff of one system, with an image and a MusicXML transcription of that grandstaff alone.


## Data structure

This dataset has **no page-level data**. OLiMPiC samples were cut out of pages that are not part of the distribution, so there is no page image and no page-level transcription to provide. Page folders are therefore empty of files and only carry subdivisions:

```
UFAL.OlimpicSynthetic/ 📚
├── musicorpus.json 🏛️
├── ...
│
└── 5026306-p5/ 📜
    ├── Grandstaves/ 🎼
    │   ├── 1/
    │   │   ├── image.jpg 🖼️
    │   │   └── transcription.musicxml 📄
    │   └── 2/
    └── Staves/ 🎼
        ├── 1a/
        │   ├── image.jpg 🖼️
        │   └── transcription.musicxml 📄
        ├── 1b/
        └── 2a/, 2b/
```

**Page names** are `{score}-p{page}`, where `{score}` is the OpenScore Lieder score identifier that OLiMPiC carries and `{page}` is the 1-based page number within that score. The page `5026306-p5` is page 5 of the score 5026306.

**Grandstaff names** are the 1-based number of the system within the page, so `Grandstaves/2` is the second system of that page. MusiCorpus recommends naming a grandstaff after the staves it spans (`1-2`, `3-4`), but that needs the staff numbering of the original page layout, which did not survive OLiMPiC's processing of the Lieder corpus. The specification's fallback of numbering grandstaves from one within the page is used instead.

**Staff names** are the name of the grandstaff they came out of, suffixed with `a` for its upper staff and `b` for its lower staff. `Staves/2a` is the upper staff of `Grandstaves/2`.


## How the staves were derived

The `Staves` subdivision is not part of OLiMPiC. It is generated from the grandstaff data by this dataset's export:

- The **transcription** is split by separating the two-staff piano part into two single-staff parts, voice by voice. Where the music cannot be separated — where a voice crosses from one staff to the other, which is ordinary in piano writing — the grandstaff is left without staves. Roughly one grandstaff in six is such a case, so `Staves` covers less of the dataset than `Grandstaves` does.
- The **image** is split by taking the upper two thirds of the grandstaff image for the upper staff and the lower two thirds for the lower staff. The two crops therefore overlap in the middle third. This is a heuristic: OLiMPiC carries no staff coordinates, and a cut at the exact halfway point would slice off stems, beams and ledger lines that reach past the staff lines. Expect some notation of the other staff to be visible at the edge of a staff image.

A staff image is consequently a *crop that contains* its staff rather than a tight crop *of* it, and the pairing between a staff image and its transcription is only as good as that heuristic. Use `Grandstaves` when this matters.


## Images

Every image is provided as `image.jpg`, as MusiCorpus requires. These JPEGs are compressed hard — OLiMPiC publishes PNG, and a faithful JPEG re-encoding of grayscale, near-bilevel music notation is several times the size of the PNG it came from. Expect visible ringing around staff lines and note heads at 1:1 zoom; every symbol remains unambiguous, and for training data this behaves as a mild augmentation.

If a lossless `image.png` sits beside an `image.jpg`, this export was built to keep the original pixels: for a grandstaff that PNG is the OLiMPiC file unchanged, and for a staff it is the lossless crop of it.


## Splits

`splits.json` carries the OLiMPiC splits, with `dev` renamed to `validation` as MusiCorpus names it. The synthetic variant is distributed with a train, a dev and a test set.

OLiMPiC splits samples where MusiCorpus splits pages. This is lossless here only because no OLiMPiC page has its systems spread across two splits, which holds for both variants as distributed.


## Licence

This dataset is available under the CC BY-SA 4.0 licence, as inherited from OLiMPiC — see `LICENSE.txt`, which is the licence file distributed with the original dataset.
