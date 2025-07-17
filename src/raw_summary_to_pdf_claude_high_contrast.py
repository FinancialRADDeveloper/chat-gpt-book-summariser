#!/usr/bin/env python3
"""
eBook Summary to PDF Converter (High Contrast Version)

This script is identical to raw_summary_to_pdf_claude.py but uses a high-contrast color scheme.
It converts markdown-formatted eBook summaries into attractive PDF documents with black headings
instead of blue, making it more readable on greyscale devices like the reMarkable tablet.

The ONLY change from the original script is the color scheme - all formatting, fonts, and
functionality remain exactly the same.

Required packages:
pip install reportlab markdown beautifulsoup4 lxml

Usage:
python raw_summary_to_pdf_claude_high_contrast.py input_file.txt output_file.pdf
python raw_summary_to_pdf_claude_high_contrast.py --folder
"""

import re
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

import markdown
from bs4 import BeautifulSoup


class EBookSummaryParser:
    """Parses and converts eBook summaries to PDF format."""

    def __init__(self):
        self.styles = self._create_styles()
        self.story = []

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for the PDF."""
        styles = getSampleStyleSheet()

        custom_styles = {
            "Title": ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                fontSize=24,
                spaceAfter=30,
                textColor=HexColor("#2E3440"),
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            ),
            "Subtitle": ParagraphStyle(
                "CustomSubtitle",
                parent=styles["Heading1"],
                fontSize=18,
                spaceAfter=20,
                spaceBefore=20,
                textColor=HexColor("#4C566A"),
                fontName="Helvetica-Bold",
            ),
            "Heading1": ParagraphStyle(
                "CustomHeading1",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=HexColor("#000000"),  # Changed from #5E81AC (blue) to #000000 (black)
                fontName="Helvetica-Bold",
            ),
            "Heading2": ParagraphStyle(
                "CustomHeading2",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
                textColor=HexColor("#222222"),  # Changed from #81A1C1 (light blue) to #222222 (dark grey)
                fontName="Helvetica-Bold",
            ),
            "Heading3": ParagraphStyle(
                "CustomHeading3",
                parent=styles["Heading3"],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                textColor=HexColor("#444444"),  # Changed from #88C0D0 (lighter blue) to #444444 (medium grey)
                fontName="Helvetica-Bold",
            ),
            "Body": ParagraphStyle(
                "CustomBody",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=6,
                spaceBefore=6,
                textColor=HexColor("#3B4252"),
                fontName="Helvetica",
                alignment=TA_JUSTIFY,
                leading=14,
            ),
            "Quote": ParagraphStyle(
                "CustomQuote",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=12,
                spaceBefore=12,
                textColor=HexColor("#4C566A"),
                fontName="Helvetica-Oblique",
                leftIndent=30,
                rightIndent=30,
                borderWidth=0,
                borderColor=HexColor("#D08770"),
                borderPadding=10,
                backColor=HexColor("#ECEFF4"),
                alignment=TA_JUSTIFY,
            ),
            "Bullet": ParagraphStyle(
                "CustomBullet",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=4,
                spaceBefore=4,
                textColor=HexColor("#3B4252"),
                fontName="Helvetica",
                leftIndent=20,
                bulletIndent=10,
                bulletFontName="Helvetica-Bold",
                bulletColor=HexColor("#000000"),  # Changed from #5E81AC (blue) to #000000 (black)
            ),
            "Emphasis": ParagraphStyle(
                "CustomEmphasis",
                parent=styles["Normal"],
                fontSize=12,
                spaceAfter=10,
                spaceBefore=10,
                textColor=HexColor("#D08770"),
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
            ),
        }

        return custom_styles

    def parse_markdown_text(self, text: str) -> str:
        """Convert markdown text to HTML, handling custom formatting."""
        # Convert markdown to HTML
        html = markdown.markdown(text, extensions=["extra", "codehilite"])

        # Parse with BeautifulSoup for easier manipulation
        soup = BeautifulSoup(html, "html.parser")

        # Convert back to string
        return str(soup)

    def extract_title(self, text: str) -> str:
        """Extract the main title from the text."""
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# ") and "BOOK SUMMARY" in line:
                # Extract book title and author
                title_match = re.search(r"# BOOK SUMMARY: (.+)", line)
                if title_match:
                    return title_match.group(1)
            elif line.startswith("# ") and line != "# BOOK SUMMARY":
                return line[2:].strip()
        return "eBook Summary"

    def process_content(self, text: str) -> List[Any]:
        """Process the text content and return story elements."""
        story = []

        # Extract title
        title = self.extract_title(text)
        story.append(Paragraph(title, self.styles["Title"]))
        story.append(Spacer(1, 20))

        # Add generation date
        date_str = f"Generated on {datetime.now().strftime('%B %d, %Y')}"
        story.append(Paragraph(date_str, self.styles["Body"]))
        story.append(Spacer(1, 30))

        # Process content line by line
        lines = text.split("\n")
        in_bullet_list = False
        current_paragraph = []

        for line in lines:
            line = line.strip()

            if not line:
                # Empty line - end current paragraph if any
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles["Body"]))
                    current_paragraph = []
                    story.append(Spacer(1, 6))
                in_bullet_list = False
                continue

            # Skip the main title line as we already processed it
            if line.startswith("# BOOK SUMMARY"):
                continue

            # Headers
            if line.startswith("###"):
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles["Body"]))
                    current_paragraph = []

                header_text = line[3:].strip()
                story.append(Paragraph(header_text, self.styles["Heading3"]))
                in_bullet_list = False

            elif line.startswith("##"):
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles["Body"]))
                    current_paragraph = []

                header_text = line[2:].strip()
                story.append(Paragraph(header_text, self.styles["Heading2"]))
                in_bullet_list = False

            elif line.startswith("#"):
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles["Body"]))
                    current_paragraph = []

                header_text = line[1:].strip()
                story.append(Paragraph(header_text, self.styles["Heading1"]))
                in_bullet_list = False

            # Bullet points
            elif line.startswith("*") or line.startswith("-"):
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles["Body"]))
                    current_paragraph = []

                bullet_text = line[1:].strip()
                # Process bold text in bullets
                bullet_text = self._process_bold_text(bullet_text)
                story.append(Paragraph(f"• {bullet_text}", self.styles["Bullet"]))
                in_bullet_list = True

            # Block quotes
            elif line.startswith(">"):
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles["Body"]))
                    current_paragraph = []

                quote_text = line[1:].strip()
                # Remove extra quotes if present
                if quote_text.startswith('"') and quote_text.endswith('"'):
                    quote_text = quote_text[1:-1]
                story.append(Paragraph(f'"{quote_text}"', self.styles["Quote"]))
                in_bullet_list = False

            # Regular text
            else:
                if in_bullet_list:
                    # Add some space after bullet lists
                    story.append(Spacer(1, 6))
                    in_bullet_list = False

                # Process bold text
                line = self._process_bold_text(line)
                current_paragraph.append(line)

        # Add any remaining paragraph
        if current_paragraph:
            paragraph_text = " ".join(current_paragraph)
            story.append(Paragraph(paragraph_text, self.styles["Body"]))

        return story

    def _process_bold_text(self, text: str) -> str:
        """Convert **bold** markdown to ReportLab bold formatting."""
        # Replace **text** with <b>text</b>
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        return text

    def create_pdf(self, input_file: str, output_file: str):
        """Create PDF from input text file."""
        # Normalize file paths for Windows
        input_file = os.path.normpath(input_file)
        output_file = os.path.normpath(output_file)

        # Read input file
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File '{input_file}' not found.")
            return
        except Exception as e:
            print(f"Error reading file: {e}")
            return

        # Create PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Process content
        story = self.process_content(content)

        # Build PDF
        try:
            doc.build(story)
            print(f"PDF successfully created: {output_file}")
        except Exception as e:
            print(f"Error creating PDF: {e}")


def process_folder(
    input_folder: str = "src/raw_summaries",
    output_folder: str = "src/claude_pdf_summaries_high_contrast",
):
    """Process all text files in the input folder and create PDFs in the output folder."""

    input_path = Path(input_folder)
    output_path = Path(output_folder)

    # Check if input folder exists
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        print("Please create the folder and add your summary files.")
        return

    # Create output folder if it doesn't exist
    output_path.mkdir(exist_ok=True)
    print(f"Output folder '{output_folder}' ready.")

    # Find all text files in the input folder
    text_files = list(input_path.glob("*.txt"))

    if not text_files:
        print(f"No .txt files found in '{input_folder}' folder.")
        return

    print(f"Found {len(text_files)} text file(s) to process:")

    # Create parser instance
    parser = EBookSummaryParser()

    # Process each file
    for text_file in text_files:
        print(f"\nProcessing: {text_file.name}")

        # Create output filename (remove _raw suffix if present and add .pdf extension)
        stem = text_file.stem
        if stem.endswith("_raw"):
            stem = stem[:-4]  # Remove the _raw suffix
        output_file = output_path / f"{stem}.pdf"

        try:
            # Convert to PDF - ensure paths are properly formatted for Windows
            input_path_str = os.path.normpath(str(text_file))
            output_path_str = os.path.normpath(str(output_file))
            parser.create_pdf(input_path_str, output_path_str)
            print(f"✓ Created: {output_file}")
        except Exception as e:
            print(f"✗ Error processing {text_file.name}: {e}")

    print(f"\nProcessing complete! PDFs saved to '{output_folder}' folder.")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert eBook summaries to formatted PDFs with high-contrast headings"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input text file containing the eBook summary (optional - will process folder if not provided)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output PDF file (optional, defaults to input filename with .pdf extension)",
    )
    parser.add_argument(
        "--folder",
        action="store_true",
        help="Process all files in raw_summaries folder",
    )

    args = parser.parse_args()

    # If no arguments provided or --folder flag used, process the folder
    if args.folder or not args.input_file:
        process_folder()
    else:
        # Single file processing (original functionality)
        # Set output file if not provided
        if not args.output_file:
            input_path = Path(args.input_file)
            # Remove _raw suffix if present
            stem = input_path.stem
            if stem.endswith("_raw"):
                stem = stem[:-4]  # Remove the _raw suffix
                args.output_file = input_path.with_name(f"{stem}.pdf")
            else:
                args.output_file = input_path.with_suffix(".pdf")

        # Create parser and generate PDF
        parser = EBookSummaryParser()
        # Ensure paths are properly formatted for Windows
        input_path_str = os.path.normpath(args.input_file)
        output_path_str = os.path.normpath(str(args.output_file))
        parser.create_pdf(input_path_str, output_path_str)


if __name__ == "__main__":
    main()


# Example usage in a script:
def example_usage():
    """Example of how to use the EBookSummaryParser class directly."""

    # Sample content (your provided example)
    sample_content = """# BOOK SUMMARY: Clean Code in Python - Mariano Anaya

## Introduction

Mariano Anaya's "Clean Code in Python" isn't just another coding style guide; it's a pragmatic deep dive into software engineering principles tailored for Python developers.

## Key Concepts and Insights

### Technical Debt and Maintainability

Anaya powerfully illustrates the hidden costs of accumulating technical debt.

> "Without quality code, the project will face the perils of failing due to an accumulated technical debt."

* **Key takeaways:**
    * Technical debt is a silent killer, leading to unexpected slowdowns and project failures.
    * Maintainable code directly translates to predictable delivery cycles and reduced risk.
    * A good understanding of clean code principles can mitigate these challenges.

### SOLID Principles

The book provides a practical guide to the **SOLID principles** which are fundamental to robust software design.

# FINAL REVIEW AND RECOMMENDATION

"Clean Code in Python" is a **highly recommended** read for any tech leader striving to build high-quality software using Python."""

    # Create parser
    parser = EBookSummaryParser()

    # Save sample content to file
    with open("sample_summary.txt", "w", encoding="utf-8") as f:
        f.write(sample_content)

    # Create PDF
    parser.create_pdf("sample_summary.txt", "sample_summary.pdf")

    print("Example PDF created: sample_summary.pdf")


def quick_folder_process():
    """Quick function to process the raw_summaries folder."""
    print("Processing all files in raw_summaries folder...")
    process_folder()


# Uncomment the line below to run the example
# example_usage()

# Uncomment the line below to quickly process the folder
# quick_folder_process()
