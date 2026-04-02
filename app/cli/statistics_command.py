import argparse
from pathlib import Path
from ..statistics.compute_statistics import compute_statistics
import yaml
import sys


def define_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to the root folder of a MusiCorpus dataset " +
            "on which to compute statistics"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to write the output YAML, uses stdout if not provided"
    )
    parser.add_argument(
        "--splits",
        type=str,
        default="splits.json",
        help="Which splits.json file to use, defaults to 'splits.json'"
    )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace):
    dataset_path = Path(args.dataset)
    output_file = None if args.output in [None, "-"] else Path(args.output)
    splits_file_name = str(args.splits)

    statistics = compute_statistics(
        dataset_path=dataset_path,
        splits_file_name=splits_file_name
    )

    # write to standard output
    if output_file is None:
        print("---")
        yaml.dump(statistics.to_yaml(), sys.stdout, indent=2, sort_keys=False)
    else: # or to an output file
        with open(output_file, "w") as f:
            yaml.dump(statistics.to_yaml(), f, indent=2, sort_keys=False)
