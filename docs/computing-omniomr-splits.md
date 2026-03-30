# Computing OmniOMR splits

OmniOMR dataset contains the `splits.json 🪓` and `splits.book-consistent.json 🪓` files. These are frozen in the folder `app/omniomr/assets` and tracked by git. This documentation page describes how you can generate them from scratch, or extend them with new pages when the dataset grows.

The split generation is done using this CLI command:

```bash
./musicorpus omniomr-splits --help
```

It requires the same page metadata CSV file that is necessary for the OmniOMR export (see [Exporting OmniOMR Dataset to MusiCorpus](exporting-omniomr-dataset.md)).

The generation of book-consistent splits (i.e. splits where all pages from one book always stay whithin one split only) is enabled by the `--book_consistent` flag.

To only add new pages to an old splits file, use the option `--extend_splits SPLITS_FILE` with path to an existing splits file.

The computation works by repeatedly generating random splits and then seeing how evenly are controlled metadata values distributed among them. It picks the most even splits version. The option `--n_attempts` controlls the number of iterations. For a production run, set this to 1 million (`1_000_000`, underscores are ok).

If the output file already exists, the `--force` flag forces its overwriting.

The size of the resulting validation and test splits is currently hard-coded inside the split generation code in `calculate_splits.py`. For small dataset, it's better when these splits are larger to get stable evaluation numbers (say 20%) and it can decrease to 15% or 10% when the total number of pages in the dataset grows.

```py
VALIDATION_FRACTION = 0.2
TEST_FRACTION = 0.2
```

---

Now with all the data ready, you can extend the existing `splits.json 🪓` file with this command:

```bash
DATE="2026-03-02"

./musicorpus omniomr-splits \
  --metadata ~/datasets/OmniOMR-Metadata/$DATE.csv \
  --page_names ~/datasets/OmniOMR-MusiCorpus/$DATE/page-names.txt \
  --extend_splits app/omniomr/assets/splits.json \
  --n_attempts 1_000_000 \
  --output app/omniomr/assets/splits.json \
  --force
```

And you can extend the `splits.book-consistent.json 🪓` file with this command:

```bash
DATE="2026-03-02"

./musicorpus omniomr-splits \
  --metadata ~/datasets/OmniOMR-Metadata/$DATE.csv \
  --page_names ~/datasets/OmniOMR-MusiCorpus/$DATE/page-names.txt \
  --extend_splits app/omniomr/assets/splits.book-consistent.json \
  --n_attempts 1_000_000 \
  --output app/omniomr/assets/splits.book-consistent.json \
  --book_consistent \
  --force
```

To generate these splits from scratch, simply remove the `--extend_splits` option.
