from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json


@dataclass
class MusicorpusManifest:
    """
    The musicorpus.json file placed in the root of dataset.
    This is its python-parsed representation.
    """

    musicorpus_version: str
    """Version of the MusiCorpus dataset format used,
    as well as the version of the musicorpus.json file format."""

    full_institution_name: str
    """Human-readable name of the institution behind the dataset."""

    short_institution_name: str
    """The first-half of the dataset folder name (i.e. *CVC*.Dolores),
    must match exactly and be a path-safe string"""

    institution_url: str
    """URL link to the website of the institution."""

    full_dataset_name: str
    """Human-readable name of the dataset."""

    short_dataset_name: str
    """The second-half of the dataset folder name (i.e. CVC.*Dolores*),
    must match exactly and be a path-safe string."""

    dataset_url: str
    """URL link to the website about the dataset
    or the project from which the dataset arose."""

    dataset_version: str
    """Version of the dataset in the {major}.{minor} format."""

    created_at: datetime
    """ISO 8601 timestamp of the moment the dataset was put together."""

    author_emails: list[str]
    """List of email addresses of authors, sorted by who
    should be emailed first/second/etc."""

    @staticmethod
    def load_from_file(file_path: Path) -> "MusicorpusManifest":
        with open(file_path, "r") as f:
            data = json.load(f)
        return MusicorpusManifest(
            musicorpus_version=str(data["musicorpus_version"]),
            full_institution_name=str(data["full_institution_name"]),
            short_institution_name=str(data["short_institution_name"]),
            institution_url=str(data["institution_url"]),
            full_dataset_name=str(data["full_dataset_name"]),
            short_dataset_name=str(data["short_dataset_name"]),
            dataset_url=str(data["dataset_url"]),
            dataset_version=str(data["dataset_version"]),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            author_emails=[str(e) for e in data["author_emails"]],
        )
    
    def write_to_file(self, file_path: Path):
        data = {
            "musicorpus_version": self.musicorpus_version,
            "full_institution_name": self.full_institution_name,
            "short_institution_name": self.short_institution_name,
            "institution_url": self.institution_url,
            "full_dataset_name": self.full_dataset_name,
            "short_dataset_name": self.short_dataset_name,
            "dataset_url": self.dataset_url,
            "dataset_version": self.dataset_version,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "author_emails": self.author_emails
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
