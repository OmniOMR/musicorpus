"""Tests for the CLI's shape.

Building the parser imports every command module, so this file also serves as
a check that the whole command layer imports cleanly.
"""

import subprocess
import sys


def test_the_cli_runs_as_a_module() -> None:
    """`python -m musicorpus` prints help and exits 2 with no arguments."""
    result = subprocess.run(
        [sys.executable, "-m", "musicorpus"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "available commands" in result.stdout


def test_every_command_answers_help() -> None:
    """Each subcommand's --help works, which means its module imports."""
    commands = [
        "validate",
        "statistics",
        "export-grandstaff",
        "export-omniomr",
        "omniomr-splits",
    ]

    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "musicorpus", command, "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"`{command} --help` failed:\n{result.stderr}"
        assert "usage:" in result.stdout
