# Exporting OmniOMR dataset to MusiCorpus

Today is `2026-03-02`, we'll make an export with this date. I will have all the data in my home directory in `~/datasets` folder. You can adjust this as you wish.

First, we need to download data from ground-truth data sources (see [Our data](https://github.com/OmniOMR/omniomr_annotation/tree/main?tab=readme-ov-file#our-data) in the private OmniOMR repo).

1. Download MuNG Studio documents from the cluster to `~/datasets/MuNG-Studio-Backups/2026-03-02`, you can use this command:

```bash
scp -pr mayer@geri.ms.mff.cuni.cz:/lnet/work/people/mayer/mung-studio-documents ~/datasets/MuNG-Studio-Backups/2026-03-02
```

2. Download MuseScore editions from Google Drive to `~/datasets/OmniOMR-Editions/2026-03-02`. Download the whole folder and then un-zip it. The `2026-03-02` folder will contain all the `[uuid_uuid].mscz` files.

```
Google Drive: Hotové revize > Download
Google Drive: zipping...
Chrome: downloading...
Open the zip-file, extract the "Hotové revize" folder
Rename the folder to "2026-03-02" and move it to "~/datasets/OmniOMR-Editions"
```

3. Download the Metadata Table from Google Drive to `~/datasets/OmniOMR-Metadata/2026-03-02.csv`.

```
Google Sheets: File > Download > Comma-separated values (.csv)
Rename the file to "2026-03-02.csv" and move it to "~/datasets/OmniOMR-Metadata"
```

4. Prepare the list of page UUIDs to be exported into a text file at `~/datasets/OmniOMR-MusiCorpus/2026-03-02/page-names.txt`, one `{UUID}_{UUID}` per line, no suffixes. Get them from the Master Table with <kbd>Ctrl+C</kbd> from Google Sheets and <kbd>Ctrl+V</kbd> into VS Code. Lines can be commented out with the hash `#` symbol.

```
# example page-names.txt file:

3bb9e322-bc61-4307-856b-6f8fb1a640df_2d5f652c-1df0-474c-ae23-3fb699afe808
48788ad8-de8b-4d01-ace1-4adffc7ed0ad_ea864792-7020-47e7-bb7b-3a48477202cf
7a040274-1704-4a21-b1c5-f48c821e3841_ced95a07-0587-473c-9c91-199a35555360
ca625f33-b4e1-49a9-bbc4-63130ba0fe70_b611e394-9858-4732-a14c-648f11497bb9
30d6c780-c8fe-11e7-9c14-005056827e51_36058ae0-f593-11e7-b30f-5ef3fc9ae867
```

Now with all the data ready, you can run the export with this command:

```bash
DATE="2026-03-02"

./musicorpus export-omniomr \
  --ms_documents ~/datasets/MuNG-Studio-Backups/$DATE \
  --ms_editions ~/datasets/OmniOMR-Editions/$DATE \
  --metadata ~/datasets/OmniOMR-Metadata/$DATE.csv \
  --page_names ~/datasets/OmniOMR-MusiCorpus/$DATE/page-names.txt \
  --output ~/datasets/OmniOMR-MusiCorpus/$DATE/UFAL.OmniOMR
```

It will create this folder `~/datasets/OmniOMR-MusiCorpus/2026-03-02/UFAL.OmniOMR`, which is the final, exported dataset. If you want to re-run the export and overwrite the output folder, add the `--force` flag.

> **Note:** The export process will also create one `.musicxml` file for each `.mscz` file in the `OmniOMR-Editions` folder.
