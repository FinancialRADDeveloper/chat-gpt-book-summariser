# article_to_pdf_v3.py
#
# This script converts a structured text file into a beautifully designed,
# magazine-style PDF article. It's designed to be generic, parsing the
# input file for titles, headings, paragraphs, and quotes.
# This version features slightly smaller section headings for a more refined look.
#
# To run this script, you first need to install the library:
# pip install fpdf2

import re
from fpdf import FPDF

# --- Configuration for Magazine Style ---
# Define a color palette for a professional look
COLOR_PALETTE = {
    "dark_blue": (22, 46, 81),
    "text_dark": (34, 34, 34),
    "text_light": (85, 85, 85),
    "line_grey": (220, 220, 220),
    "quote_grey": (240, 240, 240)
}


class PDF(FPDF):
    """
    Custom PDF class to create a consistent magazine-style layout.
    Includes a custom header for the title banner on the first page
    and a standard footer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.article_title = ""
        self.article_subtitle = ""

    def set_article_meta(self, title, subtitle):
        """Sets the title and subtitle for the header."""
        self.article_title = title
        self.article_subtitle = subtitle

    def header(self):
        """
        Creates the main title banner on the first page only.
        Subsequent pages will have a simple header.
        """
        if self.page_no() == 1:
            # --- Magazine Title Banner ---
            self.set_fill_color(*COLOR_PALETTE["dark_blue"])
            # Draw the banner rectangle
            self.rect(0, 0, self.w, 50, 'F')

            # --- Article Title ---
            self.set_y(15)
            self.set_font('Helvetica', 'B', 24)
            self.set_text_color(255, 255, 255)  # White text
            self.multi_cell(0, 10, self.article_title, 0, 'C')
            self.ln(2)

            # --- Article Subtitle ---
            self.set_y(35)
            self.set_font('Helvetica', 'I', 11)
            self.set_text_color(200, 200, 200)  # Light grey text
            self.multi_cell(0, 5, self.article_subtitle, 0, 'C')

            # Set top margin for the content after the banner
            self.set_top_margin(65)
            self.set_y(65)
        else:
            # Simple header for subsequent pages
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(*COLOR_PALETTE["text_light"])
            self.cell(0, 10, self.article_title, 0, 0, 'L')
            self.set_y(self.get_y() + 10)

    def footer(self):
        """Standard footer with page number."""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*COLOR_PALETTE["text_light"])
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def draw_section_separator(self):
        """Draws a light grey line to separate sections."""
        self.ln(5)
        self.set_draw_color(*COLOR_PALETTE["line_grey"])
        self.cell(0, 0, '', 'T', 1)
        self.ln(5)

    def show_heading(self, text):
        """Formats and displays a section heading."""
        # UPDATED: Font size reduced from 16 to 14
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*COLOR_PALETTE["dark_blue"])
        self.multi_cell(0, 10, text, 0, 'L')
        self.ln(2)

    def show_paragraph(self, text):
        """Formats and displays a standard paragraph."""
        self.set_font('Times', '', 12)
        self.set_text_color(*COLOR_PALETTE["text_dark"])
        self.multi_cell(0, 7, text, 0, 'J')  # Justified text
        self.ln(4)

    def show_quote(self, text):
        """Formats and displays a quote in a styled block."""
        self.ln(2)
        quote_x = self.get_x()
        quote_y = self.get_y()
        self.set_left_margin(self.l_margin + 5)  # Indent text

        # Draw background box for the quote
        self.set_fill_color(*COLOR_PALETTE["quote_grey"])
        # We need to calculate the height of the quote first
        temp_pdf = self.__class__()  # Create temp instance to calculate height
        temp_pdf.add_page()
        temp_pdf.set_font('Times', 'I', 11)
        temp_pdf.set_left_margin(self.l_margin + 5)
        temp_pdf.multi_cell(0, 6, text, 0, 'L')
        quote_height = temp_pdf.get_y() - temp_pdf.t_margin

        self.rect(quote_x, quote_y, self.w - self.l_margin - self.r_margin, quote_height + 4, 'F')

        # Draw vertical accent line
        self.set_draw_color(*COLOR_PALETTE["dark_blue"])
        self.set_line_width(1)
        self.line(quote_x, quote_y, quote_x, quote_y + quote_height + 4)

        # Set quote text
        self.set_y(quote_y + 2)  # Add padding
        self.set_font('Times', 'I', 11)
        self.set_text_color(*COLOR_PALETTE["text_light"])
        self.multi_cell(0, 6, text, 0, 'L')

        self.set_left_margin(self.l_margin)  # Reset margin
        self.ln(6)


def parse_summary_file(filepath):
    """
    Parses a text file with simple markdown-like syntax.
    - The first line starting with '#' is the title.
    - Lines starting with '##' are main section headers.
    - Lines starting with '###' are subsection headers.
    - Lines starting with '>' are quotes.
    - Other non-empty lines are paragraphs.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    article_data = {
        "title": "Untitled Article",
        "subtitle": "",
        "content": []
    }

    # Use a copy of lines to find and remove the title line
    processing_lines = list(lines)
    title_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith('# ') and not title_found:
            article_data["title"] = line.lstrip('# ').strip()
            processing_lines.pop(i)  # Remove title from the lines to be processed
            title_found = True
            break

    # Parse the content line by line from the remaining lines
    paragraph_buffer = []
    for line in processing_lines:
        line = line.strip()
        if not line:  # Empty line = end of paragraph
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            continue

        if line.startswith('## '):  # Main header logic
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("header", line.lstrip('## ').strip()))
        elif line.startswith('### '):  # Subsection headers
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("subheader", line.lstrip('### ').strip()))
        elif line.startswith('> '):  # Block quotes
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("quote", line.lstrip('> ').strip()))
        else:  # Regular paragraph
            paragraph_buffer.append(line)

    # Add any remaining paragraph
    if paragraph_buffer:
        article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))

    return article_data


def create_article_pdf(article_data, filename="magazine_article.pdf"):
    """
    Generates the PDF file from the parsed article data.
    """

    def sanitize_text(text):
        """Utility to replace unsupported characters."""
        unicode_map = {
            "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
            "\u2014": "--", "\u2026": "..."
        }
        for unicode_char, ascii_char in unicode_map.items():
            text = text.replace(unicode_char, ascii_char)
        return text.encode("latin-1", "replace").decode("latin-1")

    pdf = PDF('P', 'mm', 'A4')
    pdf.set_article_meta(article_data["title"], article_data["subtitle"])
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    first_heading = True
    for content_type, text in article_data["content"]:
        sanitized_text = sanitize_text(text)
        if content_type == "header":  # Main section headers (##)
            if not first_heading:
                pdf.draw_section_separator()
            pdf.show_heading(sanitized_text)
            first_heading = False
        elif content_type == "subheader":  # Subsections (including 'Introduction')
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*COLOR_PALETTE["text_dark"])
            pdf.multi_cell(0, 7, sanitized_text, 0, 'L')  # Slightly smaller font for subsections
            pdf.ln(2)
        elif content_type == "paragraph":  # Regular paragraph
            pdf.show_paragraph(sanitized_text)
        elif content_type == "quote":  # Block quotes
            pdf.show_quote(sanitized_text)

    try:
        pdf.output(filename)
        print(f"Successfully created beautiful magazine article: {filename}")
    except Exception as e:
        print(f"An error occurred while creating the PDF: {e}")


if __name__ == '__main__':
    # Get a list of files in the raw_summaries directory
    import os

    raw_summaries_dir = "raw_summaries"

    for filename in os.listdir(raw_summaries_dir):
        if filename.endswith(".txt"):
            # Get the input file path
            input_file = os.path.join(raw_summaries_dir, filename)

            # Generate output PDF filename by replacing .txt extension
            output_filename = os.path.splitext(filename)[0] + ".pdf"

            # Parse the summary file into a structured format
            parsed_data = parse_summary_file(input_file)

            # Generate the beautiful PDF from the parsed data
            create_article_pdf(parsed_data, filename=os.path.join('summaries', output_filename))