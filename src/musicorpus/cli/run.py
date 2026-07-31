import argparse
import sys
from collections.abc import Callable

from . import (
    export_grandstaff_command,
    export_omniomr_command,
    omniomr_splits_command,
    statistics_command,
    validate_command,
)


def run() -> None:
    """Entry point of the `musicorpus` command line tool."""

    parser = argparse.ArgumentParser(
        prog="musicorpus",
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


    # === validate ===

    validate_command.define_parser(
        subparsers.add_parser(
            "validate",
            aliases=[],
            description=
                "Validates a MusiCorpus dataset, checks that it has proper structure"
        )
    )
    root_command_handlers["validate"] = validate_command.execute

    # === statistics ===

    statistics_command.define_parser(
        subparsers.add_parser(
            "statistics",
            aliases=[],
            description=
                "Computes statistics for a MusiCorpus dataset"
        )
    )
    root_command_handlers["statistics"] = statistics_command.execute


    # === export GrandStaff ===

    export_grandstaff_command.define_parser(
        subparsers.add_parser(
            "export-grandstaff",
            aliases=[],
            description=
                "Exports GrandStaff dataset to the MusiCorpus format"
        )
    )
    root_command_handlers["export-grandstaff"] = export_grandstaff_command.execute


    # === export OmniOMR ===

    export_omniomr_command.define_parser(
        subparsers.add_parser(
            "export-omniomr",
            aliases=[],
            description=
                "Exports OmniOMR data to the MusiCorpus format"
        )
    )
    root_command_handlers["export-omniomr"] = export_omniomr_command.execute


    # === define OmniOMR splits ===

    omniomr_splits_command.define_parser(
        subparsers.add_parser(
            "omniomr-splits",
            aliases=[],
            description=
                "Utility for computing OmniOMR splits files."
        )
    )
    root_command_handlers["omniomr-splits"] = omniomr_splits_command.execute


    ######################
    # Execute the parser #
    ######################

    args = parser.parse_args()

    if args.root_command_name is None:
        parser.print_help()
        sys.exit(2)

    root_command_handlers[str(args.root_command_name)](parser, args)
