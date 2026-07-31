"""Turning a missing optional dependency into an answer rather than a traceback.

Reading a MusiCorpus dataset needs nothing but the standard library, so the
package declares no dependencies and puts everything heavier behind extras.
That means a command can be typed by somebody who has not installed what it
needs, and `ModuleNotFoundError: No module named 'mung'` is not a useful thing
to say to them.

Each command wraps its deferred imports in `requires`, naming the extra that
supplies them:

    def execute(parser, args):
        with requires("validation"):
            from ..validation.validate_dataset import validate_dataset
"""

import sys
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def requires(extra: str) -> Iterator[None]:
    """Report a missing optional dependency as the extra that would install it."""
    try:
        yield
    except ImportError as error:
        module = getattr(error, "name", None) or "a required package"
        print(
            f"This command needs the '{extra}' extra, which is not installed.\n"
            f"\n"
            f"    pip install 'musicorpus[{extra}]'\n"
            f"\n"
            f"(missing module: {module})",
            file=sys.stderr,
        )
        sys.exit(1)
