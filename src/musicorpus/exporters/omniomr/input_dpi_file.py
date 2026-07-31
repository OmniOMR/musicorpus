from pathlib import Path
import csv


class InputDpiFile:
    """Parsed representation of the input page-DPI CSV file."""
    def __init__(self, dpis: dict[str, int]):
        self.dpis = dpis
    
    @staticmethod
    def load(file_path: Path):
        dpis: dict[str, int] = {}
        with open(file_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # skip empty rows
                if row["DPI"] == "":
                    continue
                
                dpis[str(row["UUID"])] = int(row["DPI"])
        return InputDpiFile(dpis)
