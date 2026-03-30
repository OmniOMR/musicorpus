from pathlib import Path
from ..Splits import Splits
from ..PageMetadata import PageMetadata, \
    NotationType, NotationComplexity, ProductionType, \
        NotationClarity, SystemsComposition
from collections import Counter, OrderedDict
from typing import get_args
import random
import tqdm
import math


# Hardcoded size ratios.
# This is what the resulting split fractions should be.
# 
# Currently rather big, since the dataset is mostly for validation
# and has only 100 pages. But later can be dropped to 15% or even 10%.
VALIDATION_FRACTION = 0.2
TEST_FRACTION = 0.2


BALANCED_METADATA: dict[str, list[str]] = OrderedDict([
    ("notation", [str(v) for v in get_args(NotationType)]),
    ("notation_complexity", [str(v) for v in get_args(NotationComplexity)]),
    ("production", [str(v) for v in get_args(ProductionType)]),
    ("clarity", [str(v) for v in get_args(NotationClarity)]),
    ("systems", [str(v) for v in get_args(SystemsComposition)]),
])
"""Which PageMetadata fields are being balanced when generating
the splits. This is an ordered dictionary mapping field names
to their tracked set of values. The order is flattened into
a list to get the distribution vector that is then used to compute
distance between two splits."""


def calculate_splits(
        page_names: list[str],
        page_metadatas: dict[str, PageMetadata],
        existing_splits: Splits,
        output_file: Path,
        n_attempts: int,
        book_consistent: bool,
):
    """
    The implementation behind the ./musicorpus omniomr-splits command
    """

    # make sure the existing splits have only the three expected splits
    assert all(
        split_name in ["train", "validation", "test"]
        for split_name in existing_splits.split_names()
    )

    # get the old and newly added page names
    old_page_names = existing_splits.get_all_page_names()
    new_page_names = [
        p for p in page_names
        if p not in old_page_names
    ]

    # compute fractions for splits on the new pages
    # so that the total matches the desired fractions
    new_validation_fraction = (
        VALIDATION_FRACTION * len(page_names) - len(existing_splits.validation)
    ) / len(new_page_names)
    new_test_fraction = (
        TEST_FRACTION * len(page_names) - len(existing_splits.test)
    ) / len(new_page_names)
    assert new_validation_fraction > 0, "Not enough new pages to hit desired fractions"
    assert new_test_fraction > 0, "Not enough new pages to hit desired fractions"

    # run the main loop of generating the best split
    best_splits: Splits | None = None
    best_splits_internal_distance = float("inf") # lower the better
    
    for seed in tqdm.tqdm(range(n_attempts), "Generating splits..."):
        
        # generate random splits
        if book_consistent:
            splits = make_random_book_consistent_splits(
                page_names=new_page_names,
                validation_fraction=new_validation_fraction,
                test_fraction=new_test_fraction,
                seed=seed
            )
            assert_splits_are_book_consistent(splits)
        else:
            splits = Splits.make_random(
                page_names=new_page_names,
                validation_fraction=new_validation_fraction,
                test_fraction=new_test_fraction,
                seed=seed
            )
        
        splits_internal_distance = calculate_internal_distance_for_splits(
            splits=splits,
            page_metadatas=page_metadatas
        )

        # remember the first or best splits
        if best_splits is None or \
        splits_internal_distance < best_splits_internal_distance:
            best_splits = splits
            best_splits_internal_distance = splits_internal_distance
            print("New distance:", best_splits_internal_distance)

    # write the final splits to the output file
    splits.write_to_file(output_file)


def calculate_internal_distance_for_splits(
        splits: Splits,
        page_metadatas: dict[str, PageMetadata]
) -> float:
    """Calculates the total distance between all pairs of splits
    metadata distributions."""
    train_dist = calculate_metadata_distribution_for_split(
        page_names=splits.train,
        page_metadatas=page_metadatas
    )
    val_dist = calculate_metadata_distribution_for_split(
        page_names=splits.validation,
        page_metadatas=page_metadatas
    )
    test_dist = calculate_metadata_distribution_for_split(
        page_names=splits.test,
        page_metadatas=page_metadatas
    )
    return (
        total_elementwise_eucleidian_distance(train_dist, val_dist)
        + total_elementwise_eucleidian_distance(val_dist, test_dist)
        + total_elementwise_eucleidian_distance(test_dist, train_dist)
    )


def total_elementwise_eucleidian_distance(
        a: list[float],
        b: list[float]
) -> float:
    """Elementwise-eucleidian distance between two vectors, then summed"""
    assert len(a) == len(b)
    return sum(
        math.sqrt((i-j) * (i-j))
        for i, j in zip(a, b)
    )


def calculate_metadata_distribution_for_split(
        page_names: list[str],
        page_metadatas: dict[str, PageMetadata]
) -> list[float]:
    """Computes a list of floats as relative frequencies of various
    metadata values respective to the size of the split."""

    # count up metadata value frequencies for all pages
    metadata_frequencies: Counter[str] = Counter()
    for page_name in page_names:
        if page_name not in page_metadatas:
            continue
        page_metadata = page_metadatas[page_name]
        
        # go over all tracked metadata fields
        for field_name in BALANCED_METADATA.keys():
            field_value: str = getattr(page_metadata, field_name)
            metadata_frequencies.update({
                f"{field_name}::{field_value}": 1
            })
    
    # convert frequencies to relative frequencies and flatten
    metadata_distribution = [
        metadata_frequencies.get(f"{field_name}::{field_value}", 0) / len(page_names)
        for field_name, field_values in BALANCED_METADATA.items()
        for field_value in field_values
    ]

    return metadata_distribution


def make_random_book_consistent_splits(
        page_names: list[str],
        validation_fraction=0.1,
        test_fraction=0.1,
        seed=42
) -> Splits:
    """Creates new random splits that are book-consistent"""
    # first, shuffle pages to randomize the following algorithm
    rng = random.Random(seed)
    shuffled_page_names = list(page_names)
    rng.shuffle(shuffled_page_names)

    # distribute pages among books
    # (book_id -> list of page_ids)
    class Book:
        def __init__(self, book_id: str):
            self.book_id = book_id
            self.page_ids: list[str] = []
        
        def __len__(self) -> int:
            return len(self.page_ids)

        @property
        def page_names(self) -> list[str]:
            return [
                self.book_id + "_" + page_id
                for page_id in self.page_ids
            ]

    books: dict[str, Book] = {}
    for page_name in shuffled_page_names:
        book_id, page_id = page_name.split("_")
        if book_id not in books:
            books[book_id] = Book(book_id)
        books[book_id].page_ids.append(page_id)

    # group books into groups of equal number of pages
    # (index equals to book size)
    largest_book_size = max(len(book) for book in books.values())
    groups: list[list[Book]] = [[] for _ in range(largest_book_size + 1)]
    for book in books.values():
        groups[len(book)].append(book)

    # distribute books into splits such that we try to match
    # the desired size distribution as closely as possible
    # (largest books to smallest to hit fractions as closely as possible)
    train_pages: list[str] = []
    validation_pages: list[str] = []
    test_pages: list[str] = []

    distributed_pages = 0
    for group in reversed(groups): # largest books to smallest
        for book in group:
            if len(validation_pages) + len(book) - 1 < distributed_pages * validation_fraction:
                validation_pages.extend(book.page_names)
            elif len(test_pages) + len(book) - 1 < distributed_pages * test_fraction:
                test_pages.extend(book.page_names)
            else:
                train_pages.extend(book.page_names)
            distributed_pages += len(book)
    assert distributed_pages == len(page_names)

    # shuffle each split
    rng.shuffle(train_pages)
    rng.shuffle(validation_pages)
    rng.shuffle(test_pages)

    # build the splits object
    splits = Splits(
        train=train_pages,
        validation=validation_pages,
        test=test_pages
    )
    splits.check_that_it_covers_page_names_exactly(page_names)
    splits.run_assertions()
    return splits


def assert_splits_are_book_consistent(splits: Splits):
    """Makes sure that books do not overlap between splits"""
    train = list(set(page_name.split("_")[0] for page_name in splits.train))
    validation = list(set(page_name.split("_")[0] for page_name in splits.validation))
    test = list(set(page_name.split("_")[0] for page_name in splits.test))
    book_splits = Splits(
        train=train,
        validation=validation,
        test=test
    )
    book_splits.run_assertions()
