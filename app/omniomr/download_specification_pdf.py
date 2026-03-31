import requests
from pathlib import Path


DOWNLOAD_URL = "https://github.com/OmniOMR/musicorpus/releases/download/specification/musicorpus-specification_1.0_2026-03-31.pdf"


def download_specification_pdf(target_path: Path):
    """Downloads the MusiCorpus specification PDF
    from github and writes it to a file"""
    print("Downloading MusiCorpus specification PDF...")
    response = requests.get(DOWNLOAD_URL)
    assert response.status_code == 200, \
        f"HTTP status code was: {response.status_code}"
    with open(target_path, "wb") as f:
        print("There are", len(response.content), "bytes in the PDF")
        f.write(response.content)
