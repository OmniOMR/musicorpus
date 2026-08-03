"""Renders the specification to HTML and PDF, for attaching to a release.

Inspired by the Smashcima docs builder:
https://github.com/OMR-Research/Smashcima/blob/main/docs_builder

Needs `pandoc` and `chromium` on the machine, which is why this is a
maintainer script run by hand rather than part of the package or of CI:

    python3 spec/build.py

The output lands next to the markdown rather than in a folder of its own, so
that the relative `<img src="musicorpus-layout-example.png">` references in
the document resolve when chromium renders it. Both outputs are gitignored;
the PDF is published as an asset on the `specification-*` release, and the
export commands download it from there — see docs/versioning-and-releases.md.
"""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent

MARKDOWN_FILE = HERE / "musicorpus-specification.md"
HTML_FILE = HERE / "musicorpus-specification.html"
PDF_FILE = HERE / "musicorpus-specification.pdf"

TITLE = "MusiCorpus Specification"


def markdown_to_html(markdown: str) -> str:
    """Converts markdown string to html string"""
    result = subprocess.run(
        # from github-flavored md to html, output to stdout
        ["pandoc", "-f", "gfm", "-t", "html", "-o", "-"],
        input=markdown.encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8")


def build_html_file(html_string: str, html_file_path: Path, title: str) -> None:
    """Writes html string to a file with proper title"""
    result = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "-c",
            "github-markdown.css",  # reference the CSS file, next to the output
            "-V",
            "pagetitle:" + title,
            "-f",
            "html",
            "-t",
            "html",
            "-o",
            "-",
        ],
        cwd=str(HERE),
        stdout=subprocess.PIPE,
        input=html_string.encode("utf-8"),
        check=True,
    )
    html_file_path.write_text(result.stdout.decode("utf-8"))


def build_pdf_file(path_html: Path, path_pdf: Path) -> None:
    """Converts the html file to a pdf file using chromium"""
    CHROME_CMD = "chromium"  # just "chrome" if you have chrome instead
    subprocess.run(
        [
            CHROME_CMD,
            "--headless",
            "--print-to-pdf=" + str(path_pdf.absolute()),
            "--no-pdf-header-footer",
            "file://" + str(path_html.absolute()),
        ],
        cwd=str(HERE),
        check=True,
    )


def main() -> None:
    print("Converting Markdown to HTML...")
    html_string = markdown_to_html(MARKDOWN_FILE.read_text("utf-8"))
    build_html_file(html_string=html_string, html_file_path=HTML_FILE, title=TITLE)

    print("Converting HTML to PDF...")
    build_pdf_file(path_html=HTML_FILE, path_pdf=PDF_FILE)

    print(f"Done: {PDF_FILE}")


if __name__ == "__main__":
    main()
