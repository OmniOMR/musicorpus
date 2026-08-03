"""The `musicorpus export` command group.

Exporters build a specific dataset from its own sources into the MusiCorpus
format. They are grouped under one command rather than sitting at the top
level so that the commands anybody can use — `validate`, `statistics` — stay
visible in `musicorpus --help` however many datasets get exporters over time.

Each exporter is a reference implementation. If you are bringing a dataset of
your own into the format, read `export_grandstaff_command.py` and the module
behind it: it is the short one.
"""

import argparse
import sys
from typing import Protocol

from . import export_grandstaff_command, export_olimpic_command, export_omniomr_command

NAME = "export"

DESCRIPTION = "Export a specific dataset into the MusiCorpus format"


class Exporter(Protocol):
    """What an exporter module has to provide to appear in `EXPORTERS`."""

    NAME: str
    """The exporter as typed, e.g. `grandstaff` in `musicorpus export grandstaff`."""

    DESCRIPTION: str
    """One line, shown in `musicorpus export --help`."""

    def define_parser(self, parser: argparse.ArgumentParser) -> None: ...

    def execute(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> None: ...


EXPORTERS: list[Exporter] = [
    export_grandstaff_command,
    export_olimpic_command,
    export_omniomr_command,
]


def define_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(title="available exporters", dest="exporter")

    for exporter in EXPORTERS:
        exporter.define_parser(
            subparsers.add_parser(
                exporter.NAME,
                description=exporter.DESCRIPTION,
                help=exporter.DESCRIPTION,
            )
        )


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.exporter is None:
        # `parser` here is the top-level parser, whose help says nothing about
        # exporters, so print the group's own help instead.
        build_group_parser().print_help()
        sys.exit(2)

    handlers = {exporter.NAME: exporter.execute for exporter in EXPORTERS}
    handlers[str(args.exporter)](parser, args)


def build_group_parser() -> argparse.ArgumentParser:
    """The `musicorpus export` parser on its own, for printing its help."""
    parser = argparse.ArgumentParser(prog="musicorpus export", description=DESCRIPTION)
    define_parser(parser)
    return parser
