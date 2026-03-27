from pathlib import Path


class ErrorBag:
    """
    Aggregates errors from any export process, logs them to console
    and finally dumps them to an output file as well.
    """
    def __init__(self) -> None:
        self.count = 0
        """Number of errors encountered"""

        self.affected_pages: list[str] = []
        """Unique list of page names that contain some errors"""
        
        self.log: list[str] = []
        """List of string messages that should be concatenated
        for the final report"""

    def add_error(self, page_name: str, message: str):
        """Adds an error into the error bag"""
        self.count += 1

        if page_name not in self.affected_pages:
            self.affected_pages.append(page_name)
        
        log_chunk = f"ERROR at {page_name}:\n" + \
            "  " + message + "\n"
        self.log.append(log_chunk)

    def write_report_if_any_errors(self, file_path: Path):
        """Writes the final error report into a file if there are some errors"""
        if self.count == 0:
            return
        
        with open(file_path, "w") as f:
            f.write("Affected Pages\n")
            f.write("==============\n")
            for page_name in self.affected_pages:
                f.write(page_name + "\n")
            
            f.write("\n")
            f.write("\n")
            f.write("Error Log\n")
            f.write("=========\n")
            for chunk in self.log:
                f.write(chunk)
        
        print(f"THERE WERE {self.count} ERRORS DURING THE EXPORT PROCESS")
        print("Error report was written to:")
        print(str(file_path.absolute()))
