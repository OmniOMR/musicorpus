# OmniOMR Dataset

The OmniOMR dataset is intended for Optical Music Recognition (OMR) usecases, particularly focused on handwritten music notation and archival manuscripts in Common Western Music Notation (CWMN). Use cases primarily include training, fine-tuning and evaluating recognition models; end-to-end, object detection, and instance segmentation.

The dataset is built around 100 representatively chosen pages of mostly handwritten music notation, taken from the Moravian Library in Brno, Czech Republic (https://www.digitalniknihovna.cz/mzk/search?access=open&doctypes=sheetmusic). Each page is annotated in the Music Notation Graph (MuNG) 2.0 format, suitable for object detection, instance segmentation and notation graph reconstruction. Each page is also transcribed using MuseScore into the MusicXML format suitable for end-to-end recognition.


## Data preparation

The Moravian Library holds over 7 000 books containing music notation, mostly handwritten (18th to 20th century). These were scanned at DPIs from 90 to 300, but mostly around 280. This dataset was created by first selecting a representative sample of individual pages from these books with balanced distribution of solo parts, piano parts, string quartets and particellas. These scans are present in this dataset in each page folder as the `image.jpg` file.

These images were manually annotated in the *MuNG Studio* annotation tool according to the *MuNG 2.0* standard to produce the page-level `transcription.mung` files. In parallel to this, pages were also manually transcribed in MuseScore 3 and 4 to produce page-level `transcription.mscz` files.

The `transcription.mscz` files were batch-converted using MuseScore 4.6.5 to MusicXML files (`transcription.musicxml`). Annotators were instructed to insert explicit system breaks so that these MusicXML files can be automatically sliced to individual systems and staves and these are harmonized with staves and systems in our MuNG annotations.

The `coco-object-detection.json` and `layout.json` files are automatically generated from MuNG transcriptions using a script and so may contain systematic conversion errors.

The `metadata.json` files were filled out manually based on the information tracked by the Moravian Libary. Special attention was given to determining DPI values. These were manually extracted using scanned color-calibration tables with rulers on the last page of each book. The DPI is important to convert from pixel-sizes to physical-sizes of objects, when harmonizing data across pages scanned with different resolution.


## Data structure

In the OmniOMR dataset, page-level data is primary and staff, grandstaff and system-level data secondary. Data subdivisions were generated automatically from the page-level data and may contain systematic errors induced by the extraction process.

Page names consist of two UUID identifiers joined together with an underscore. The first one is the UUID of the book and the second one is the UUID of the page. When browsing the Moravian Library, you can see both UUIDs in the URL, e.g.:

```
https://www.digitalniknihovna.cz/mzk/view/uuid:bf5ef9ce-00ba-4c9f-bbb3-57e542354222?page=uuid:be64bc51-384b-48cc-a845-69e208410aa5
```

Staff, grandstaff and system names consist of ranges of staff numbers on the page. Staves are numbered 1 to N on the page going top-down, including empty and unused staves. This scheme follows MusiCorpus format recommendations.

The dataset is homogenous across pages, meaning each page provides the same set of annotation files.


## Various

All the images behind the dataset are accessible online via the Moravian Library website. The URL above uses both the book UUID and the page UUID, however, only the page UUID is needed to uniquely identify a page globally. The following URL acts as a permalink to a page with the given UUID:

```
https://www.digitalniknihovna.cz/mzk/uuid/uuid:be64bc51-384b-48cc-a845-69e208410aa5
```

The OmniOMR dataset deviates from the MusiCorpus specificion in the `layout.json` files. We provide the `staff`, `emptyStaff`, `grandstaff` and `system` annotations, but do NOT provide the measure-level annotations. Those could, however, be extracted from MuNG files if needed.

The `metadata.json/date` field does not contain specific years for many pages, since it was difficult to recover those. Instead it contains the best estimates we were able to recover from the library metadata. It must be post-processed by a human to be truly machine-readable.

The `metadata.json/scribal_data` field does not contain complete writer IDs. Given the origin of the data it was difficult to narrow down a specific person, but we still provide the most specific identification we were able to recover. It can be used as a base from which to construct proper identifiers should you need this dataset for writer identification tasks.


## Licensing

The dataset is provided under the [CC BY-NC-SA 4.0 license](https://creativecommons.org/licenses/by-nc-sa/4.0/) (see `LICENSE.txt`).

All of the files are provided under this license, including the page scans, manually annotated transcriptions and automatically generated files.


## Acknowledgement

This work has been supported by the Ministry of Culture of the Czech Republic (project NAKI no. DH23P03OVV008).

A special thanks goes to all of the annotators who collectively spent hundreds of hours making this dataset a reality.

The OmniOMR project: https://ufal.mff.cuni.cz/grants/omniomr
