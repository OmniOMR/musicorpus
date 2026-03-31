# Inspired by the Smashcima docs builder:
# https://github.com/OMR-Research/Smashcima/blob/main/docs_builder
#
# Requires the "pandoc" CLI tool to be present on the machine.
#
# Run from the repo root like this:
#   python3 -m docs_builder

from pathlib import Path
import subprocess


def markdown_to_html(markdown: str) -> str:
    """Converts markdown string to html string"""
    result = subprocess.run(
        # from github-flavored md to html, output to stdout
        [
            "pandoc",
            "-f", "gfm", "-t", "html",
            "-o", "-"
        ],
        input=markdown.encode("utf-8"),
        stdout=subprocess.PIPE
    )
    return result.stdout.decode("utf-8")


def build_html_file(
    html_string: str,
    html_file_path: Path,
    title: str
):
    """Writes html string to a file with proper title"""
    result = subprocess.run(
        [
            "pandoc", "--standalone",
            "-c", "github-markdown.css", # reference the CSS file
            "-V", "pagetitle:" + title,
            "-f", "html", "-t", "html",
            "-o", "-"
        ],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        input=html_string.encode("utf-8")
    )
    complete_html = result.stdout.decode("utf-8")
    html_file_path.write_text(complete_html)


def build_pdf_file(path_html: Path, path_pdf: Path):
    """Converts the html file to a pdf file using chromium"""
    CHROME_CMD = "chromium" # just "chrome" if you have chrome instead
    subprocess.run(
        [
            CHROME_CMD, "--headless",
            "--print-to-pdf=" + str(path_pdf.absolute()),
            "--no-pdf-header-footer",
            "file://" + str(path_html.absolute())
        ],
        cwd=str(Path(__file__).parent)
    )


def main():
    markdown_file_path = Path(__file__).parent.parent / "docs" / "musicorpus-specification" / "musicorpus-specification.md"
    html_file_path = Path(__file__).parent / "musicorpus-specification.html"
    pdf_file_path = Path(__file__).parent / "musicorpus-specification.pdf"
    
    markdown_string = markdown_file_path.read_text("utf-8")
    print("Converting Markdown to HTML...")
    html_string = markdown_to_html(markdown_string)
    build_html_file(
        html_string=html_string,
        html_file_path=html_file_path,
        title="MusiCorpus Specification"
    )
    print("Converting HTML to PDF...")
    build_pdf_file(
        path_html=html_file_path,
        path_pdf=pdf_file_path
    )
    print("Done.")


# run all magic
main()
