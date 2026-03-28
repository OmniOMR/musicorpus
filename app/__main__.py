import argparse
from typing import Callable

parser = argparse.ArgumentParser(
    prog="./musicorpus",
    description="CLI for working with the MusiCorpus format"
)

subparsers = parser.add_subparsers(
    title="available commands",
    dest="root_command_name"
)

root_command_handlers: dict[
    str,
    Callable[[argparse.ArgumentParser, argparse.Namespace], None]
] = {}


############################
# Define all root commands #
############################


# === export OmniOMR ===

import app.cli.export_omniomr_command
app.cli.export_omniomr_command.define_parser(
    subparsers.add_parser(
        "export-omniomr",
        aliases=[],
        description=
            "Exports OmniOMR data to the MusiCorpus format"
    )
)
root_command_handlers["export-omniomr"] = app.cli.export_omniomr_command.execute


# === define OmniOMR splits ===

import app.cli.omniomr_splits_command
app.cli.omniomr_splits_command.define_parser(
    subparsers.add_parser(
        "omniomr-splits",
        aliases=[],
        description=
            "Utility for computing OmniOMR splits files."
    )
)
root_command_handlers["omniomr-splits"] = app.cli.omniomr_splits_command.execute


######################
# Execute the parser #
######################

args = parser.parse_args()

if args.root_command_name is None:
    parser.print_help()
    exit(2)

root_command_handlers[str(args.root_command_name)](parser, args)
