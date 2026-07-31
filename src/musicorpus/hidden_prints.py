import os, sys

class HiddenPrints:
    """
    Disables print() calls within the wrapped code block. Usage:

    with HiddenPrints():
        do_stuff()

    https://stackoverflow.com/questions/8391411/how-to-block-calls-to-print
    """
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
