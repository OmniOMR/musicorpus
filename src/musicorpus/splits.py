from typing import Iterable
from pathlib import Path
import random
import json


class Splits:
    """
    Represents one set of splits of a MusiCorpus dataset.
    These are usually stored in splits.json file in the dataset root.
    One split is a list[str] meaning a list of page names.
    The order page names is tracked and should be shuffled
    randomly so that the user can immediately train on the split.
    (i.e. we represent it as a list, not as a set)
    """
    def __init__(
            self,
            train: list[str] | None,
            validation: list[str] | None,
            test: list[str] | None,
            **kwargs
    ):
        """
        Creates a new set of splits. Train, validation and test
        are highly recommended and additional splits can be
        passed as additional kwargs arguments. All must be of
        type list[str], representing a list of page names.
        """
        self._splits: dict[str, list[str]] = {}

        self["train"] = train
        self["validation"] = validation
        self["test"] = test
        for split_name, additional_split in kwargs.items():
            self[split_name] = additional_split
    
    @staticmethod
    def make_empty() -> "Splits":
        """Creates an empty splits file"""
        return Splits(train=[], validation=[], test=[])
    
    @staticmethod
    def make_random(
        page_names: list[str],
        validation_fraction=0.1,
        test_fraction=0.1,
        seed=42
    ) -> "Splits":
        """
        Creates random splits from given page names with
        split size fractions specified via arguments.
        """
        rng = random.Random(seed)

        shuffled_pages = list(page_names)
        rng.shuffle(shuffled_pages)

        total_size = len(shuffled_pages)
        validation_size = int(total_size * validation_fraction)
        test_size = int(total_size * test_fraction)

        return Splits(
            test=shuffled_pages[:test_size],
            validation=shuffled_pages[test_size:test_size+validation_size],
            train=shuffled_pages[test_size+validation_size:]
        )

    def split_names(self) -> Iterable[str]:
        """Iterable for all defined split names in these splits"""
        return self._splits.keys()
    
    def __contains__(self, split_name: str) -> bool:
        """Checks whether a split is defined in these splits"""
        return split_name in self._splits

    def __getitem__(self, split_name: str) -> list[str]:
        """Returns a split of a given name or raises error if missing"""
        if split_name not in self._splits:
            raise KeyError(f"Split {split_name} does not exist.")
        return self._splits[split_name]
    
    def __setitem__(self, split_name: str, value: list[str] | None):
        """Sets a split value, if None, deletes the split"""
        if value is None:
            del self[split_name]
            return
        else:
            assert type(value) is list, \
                "Given split is not a list"
            assert all(type(v) is str for v in value), \
                "Not all items in the given split are strings"
            self._splits[split_name] = value
    
    def __delitem__(self, split_name: str):
        """Deletes the given split"""
        del self._splits[split_name]
    
    def get_all_page_names(self) -> list[str]:
        """Returns all page names tracked in all the splits"""
        page_names = list()
        for split_name in self.split_names():
            page_names.extend(self[split_name])
        return page_names

    # === quick accessors for common splits ===

    @property
    def train(self) -> list[str]:
        return self["train"]
    
    @train.setter
    def train(self, value: list[str] | None):
        self["train"] = value

    @property
    def validation(self) -> list[str]:
        return self["validation"]
    
    @validation.setter
    def validation(self, value: list[str] | None):
        self["validation"] = value

    @property
    def test(self) -> list[str]:
        return self["test"]
    
    @test.setter
    def test(self, value: list[str] | None):
        self["test"] = value
    
    # === IO ===

    def write_to_file(self, file_path: Path, run_assertions=True):
        """Writes the splits to a given splits.json file"""
        if run_assertions:
            self.run_assertions()
        with open(file_path, "w") as f:
            json.dump(self._splits, f, indent=4)

    @staticmethod
    def read_from_file(file_path: Path, run_assertions=True) -> "Splits":
        with open(file_path, "r") as f:
            _splits = json.load(f)
            splits = Splits(**_splits)
            if run_assertions:
                splits.run_assertions()
            return splits
    
    # === Assertions ===

    def run_assertions(self):
        """Runs verification logic that invariants about splits hold"""
        self._assert_disjoint_splits("train", "validation")
        self._assert_disjoint_splits("train", "test")
        self._assert_disjoint_splits("validation", "test")

    def _assert_disjoint_splits(self, first_split: str, second_split: str):
        """
        Verifies that the two given splits have disjoint page names.
        If one of the splits does not exist, it does nothing.
        """
        if first_split not in self: return
        if second_split not in self: return
        overlap = set(self[first_split]) \
            .intersection(set(self[second_split]))
        assert len(overlap) == 0, \
            f"The splits {first_split} and {second_split} overlap " + \
            f"in these pages: {repr(list(overlap))}"

    def check_that_it_covers_page_names_exactly(
            self,
            page_names: list[str],
            raise_on_failure=True
    ) -> bool:
        """Checks that these splits cover given page names exactly
        (no more pages in our splits, no less pages in our splits).
        This method raises an exception when the condition fails,
        or optionally may return a boolean for success instead."""
        self.run_assertions()
        assert len(set(page_names)) == len(page_names), \
            "Given page names contain duplicates"
        
        page_set = set(page_names)
        splits_page_set = set(self.get_all_page_names())
        
        extra_pages = page_set.difference(splits_page_set)
        extra_split_pages = splits_page_set.difference(page_set)
        
        if raise_on_failure:
            assert len(extra_pages) == 0, \
                f"These page names are not covered by " + \
                f"these splits: {repr(extra_pages)}"
            assert len(extra_split_pages) == 0, \
                f"These page names are present in these splits " + \
                f"but missing from the given pages: {repr(extra_split_pages)}"
        
        return len(extra_pages) == 0 and len(extra_split_pages) == 0
