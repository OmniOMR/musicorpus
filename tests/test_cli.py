"""Tests for the command registry and the CLI's naming conventions.

Building the parser imports every command module, so this whole file runs in
milliseconds. That is itself worth protecting: a stray top-level `import mung`
in a command module would put seconds in front of `musicorpus --help`.
"""

import argparse
import re
import subprocess
import sys

import pytest

from musicorpus.cli.export_command import EXPORTERS, Exporter
from musicorpus.cli.run import COMMANDS, Command, build_parser

KEBAB_CASE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

ALL_COMMANDS: list[Command | Exporter] = [*COMMANDS, *EXPORTERS]


@pytest.mark.parametrize("command", ALL_COMMANDS, ids=lambda command: command.NAME)
def test_every_command_declares_itself(command: Command | Exporter) -> None:
    assert isinstance(command.NAME, str) and command.NAME
    assert isinstance(command.DESCRIPTION, str) and command.DESCRIPTION


@pytest.mark.parametrize("command", ALL_COMMANDS, ids=lambda command: command.NAME)
def test_command_names_are_kebab_case(command: Command | Exporter) -> None:
    assert KEBAB_CASE.match(command.NAME)


def test_command_names_are_unique() -> None:
    for group in (COMMANDS, EXPORTERS):
        names = [command.NAME for command in group]

        assert len(set(names)) == len(names)


def test_the_parser_builds() -> None:
    assert build_parser() is not None


def collect_option_strings(parser: argparse.ArgumentParser) -> list[str]:
    """Every `--flag` the parser and its subparsers accept, at any depth."""
    options: list[str] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subparser in action.choices.values():
                options.extend(collect_option_strings(subparser))
        options.extend(option for option in action.option_strings if option.startswith("--"))
    return options


def test_no_flag_is_spelled_with_an_underscore() -> None:
    """Flags are kebab-case, as they are in Zeus and Musibot.

    argparse turns `--page-names` into `args.page_names` by itself, so this is
    purely about what a user types.
    """
    underscored = sorted(
        {option for option in collect_option_strings(build_parser()) if "_" in option}
    )

    assert underscored == []


# The whole dependency stack — mung, music21, opencv, pycocotools — belongs
# inside the commands that use it. Importing any of it to build the parser
# would be paid by every invocation, including `--help` and `--version`.
HEAVY_MODULES = [
    "converter21",
    "cv2",
    "imagesize",
    "lmx",
    "mung",
    "music21",
    "numpy",
    "pycocotools",
    "requests",
    "tqdm",
    "yaml",
]


def test_building_the_parser_imports_nothing_heavy() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\n"
            "from musicorpus.cli.run import build_parser\n"
            "build_parser()\n"
            f"heavy = [m for m in {HEAVY_MODULES!r} if m in sys.modules]\n"
            "print(','.join(heavy))\n",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"building the parser imported: {result.stdout.strip()} — "
        "move those imports inside the command's execute()"
    )


def test_the_cli_runs_as_a_module() -> None:
    """`python -m musicorpus` prints help and exits 2 with no arguments."""
    result = subprocess.run(
        [sys.executable, "-m", "musicorpus"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "available commands" in result.stdout


def test_the_export_group_prints_its_own_help() -> None:
    """`musicorpus export` with no exporter lists the exporters, not the root help."""
    result = subprocess.run(
        [sys.executable, "-m", "musicorpus", "export"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "available exporters" in result.stdout


def test_every_command_answers_help() -> None:
    """Each subcommand's --help works, which means its module imports."""
    invocations = [
        ["validate"],
        ["statistics"],
        ["omniomr-splits"],
        ["export"],
        ["export", "grandstaff"],
        ["export", "omniomr"],
    ]

    for invocation in invocations:
        result = subprocess.run(
            [sys.executable, "-m", "musicorpus", *invocation, "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"`{' '.join(invocation)} --help` failed:\n{result.stderr}"
        assert "usage:" in result.stdout
