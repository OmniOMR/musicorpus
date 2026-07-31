from pathlib import Path


def read_page_names(file_path: Path) -> list[str]:
    """
    Loads page-names.txt file where there is one page name per line.
    Empty lines and lines starting with '#' are ignored. Lines are
    also trimmed of whitespace. Moreover it also checks that page
    name contain no duplicates.
    """
    # read page names
    with open(file_path) as f:
        page_names = [
            line.strip()
            for line in f.readlines()
            if line.strip() != "" and not line.startswith("#")
        ]

    # check for duplicates
    page_names_set = set(page_names)
    page_names_copy = list(page_names)
    for page_name in page_names_set:
        page_names_copy.remove(page_name)
    assert len(page_names_copy) == 0, "Page names contain these duplicates: " + repr(
        page_names_copy
    )

    return page_names
