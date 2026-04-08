import argparse
from pathlib import Path
from ..ErrorBag import ErrorBag
from ..validation.validate_dataset import validate_dataset


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
        required=True,
        help="Where to write the output validation log"
    )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace):
    dataset_path = Path(args.dataset)
    output_file = Path(args.output)

    if not dataset_path.exists():
        print("The given dataset folder does not exist.")
        return
    
    if not output_file.parent.exists():
        print("The given output path parent directory does not exist.")
        return

    errors = ErrorBag()

    validate_dataset(
        dataset_path=dataset_path,
        errors=errors
    )

    if errors.count == 0:
        print("Perfect dataset with no errors!")
        return
    else:
        errors.write_report_if_any_errors(output_file)
