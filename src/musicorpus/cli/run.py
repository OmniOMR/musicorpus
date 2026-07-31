"""The `musicorpus` command line tool.

Each command lives in a module of its own that declares its own `NAME` and
`DESCRIPTION` and provides `define_parser` and `execute`. This module only
collects them; adding a command means writing that module and naming it in
`COMMANDS` below.

None of the command modules imports mung, music21, opencv or pycocotools at
module level — each defers those into its `execute` — so building the whole
parser stays cheap and `musicorpus --help` answers immediately. A test guards
that.
"""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Protocol

from . import export_command, omniomr_splits_command, statistics_command, validate_command


class Command(Protocol):
    """What a command module has to provide to appear in `COMMANDS`."""

    NAME: str
    """The subcommand as typed, e.g. `omniomr-splits`."""

    DESCRIPTION: str
    """One line, shown both in `musicorpus --help` and in the command's own help."""

    def define_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add this command's arguments to its subparser."""
        ...

    def execute(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
        """Run the command."""
        ...


COMMANDS: list[Command] = [
    validate_command,
    statistics_command,
    export_command,
    omniomr_splits_command,
]


def package_version() -> str:
    """The installed version, or a placeholder when running from a source tree."""
    try:
        return version("musicorpus")
    except PackageNotFoundError:
        return "unknown (not installed)"


def build_parser() -> argparse.ArgumentParser:
    """Assemble the whole CLI, one subparser per command."""
    parser = argparse.ArgumentParser(
        prog="musicorpus",
        description="CLI for working with the MusiCorpus format",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
        help="Print the version of the musicorpus package and exit",
    )
    subparsers = parser.add_subparsers(title="available commands", dest="command")

    for command in COMMANDS:
        command.define_parser(
            subparsers.add_parser(
                command.NAME,
                # `description` heads the command's own --help; `help` is the
                # line beside its name in `musicorpus --help`, which listed
                # bare command names and no explanation before.
                description=command.DESCRIPTION,
                help=command.DESCRIPTION,
            )
        )

    return parser


def run() -> None:
    """Entry point of the `musicorpus` command line tool."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(2)

    handlers = {command.NAME: command.execute for command in COMMANDS}
    handlers[str(args.command)](parser, args)
