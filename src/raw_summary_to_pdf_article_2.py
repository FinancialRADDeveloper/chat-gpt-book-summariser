# article_to_pdf_v3.py
#
# This script converts a structured text file into a beautifully designed,
# magazine-style PDF article using standard, built-in fonts.
# This version handles bold prefixes in paragraphs and bullet points.
#
# To run this script, you only need to install the fpdf2 library:
# pip install fpdf2

import re
import os
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
        """Creates the main title banner on the first page only."""
        if self.page_no() == 1:
            self.set_fill_color(*COLOR_PALETTE["dark_blue"])
            self.rect(0, 0, self.w, 50, 'F')
            self.set_y(15)
            self.set_font('Helvetica', 'B', 24)
            self.set_text_color(255, 255, 255)
            self.multi_cell(0, 10, self.article_title, 0, 'C')
            self.ln(2)
            self.set_y(35)
            self.set_font('Helvetica', 'I', 11)
            self.set_text_color(200, 200, 200)
            self.multi_cell(0, 5, self.article_subtitle, 0, 'C')
            self.set_top_margin(65)
            self.set_y(65)
        else:
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
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*COLOR_PALETTE["dark_blue"])
        self.multi_cell(0, 10, text, 0, 'L')
        self.ln(2)

    def show_paragraph(self, text):
        """Formats and displays a standard paragraph, handling bold prefixes."""
        self.ln(2)
        self.set_text_color(*COLOR_PALETTE["text_dark"])
        # Check for the pattern **Bold Text** followed by more text
        match = re.match(r'\*\*(.*?)\*\*(.*)', text)
        if match:
            bold_part = match.group(1).strip()
            regular_part = match.group(2).strip()

            self.set_font('Times', 'B', 12)
            self.write(h=7, txt=bold_part + ' ')

            end_of_bold_x = self.get_x()
            self.set_font('Times', '', 12)

            remaining_width = self.w - self.r_margin - end_of_bold_x
            self.multi_cell(w=remaining_width, h=7, txt=regular_part, align='L')
        else:
            self.set_font('Times', '', 12)
            self.multi_cell(0, 7, text, 0, 'J')
        self.ln(2)

    def show_bullet_point(self, text):
        """Formats and displays a bullet point, handling bold prefixes."""
        self.ln(1)
        self.set_text_color(*COLOR_PALETTE["text_dark"])

        bullet_x = self.get_x()
        bullet_char = chr(149)
        text_x = bullet_x + 8

        # Place the bullet, but preserve Y coordinate
        current_y = self.get_y()
        self.cell(w=8, h=7, txt=bullet_char, align="C")
        self.set_y(current_y)  # Reset Y to the start of the line
        self.set_x(text_x)

        # Check for the pattern **Bold Text** followed by more text
        match = re.match(r'\*\*(.*?)\*\*(.*)', text)
        if match:
            bold_part = match.group(1).strip()
            regular_part = match.group(2).strip()

            self.set_font('Times', 'B', 12)
            self.write(h=7, txt=bold_part + ' ')

            end_of_bold_x = self.get_x()
            self.set_font('Times', '', 12)

            # Use multi_cell for the rest of the text to handle wrapping
            remaining_width = self.w - self.r_margin - end_of_bold_x
            self.multi_cell(w=remaining_width, h=7, txt=regular_part, align='L')
        else:
            self.set_font('Times', '', 12)
            self.multi_cell(0, 7, text, align='J')

        self.ln(1)

    def show_quote(self, text):
        """Formats and displays a quote in a styled block."""
        self.ln(2)
        quote_x = self.get_x()
        quote_y = self.get_y()
        self.set_left_margin(self.l_margin + 5)
        self.set_fill_color(*COLOR_PALETTE["quote_grey"])
        temp_pdf = self.__class__()
        temp_pdf.add_page()
        temp_pdf.set_font('Times', 'I', 11)
        temp_pdf.set_left_margin(self.l_margin + 5)
        temp_pdf.multi_cell(0, 6, text, 0, 'L')
        quote_height = temp_pdf.get_y() - temp_pdf.t_margin
        self.rect(quote_x, quote_y, self.w - self.l_margin - self.r_margin, quote_height + 4, 'F')
        self.set_draw_color(*COLOR_PALETTE["dark_blue"])
        self.set_line_width(1)
        self.line(quote_x, quote_y, quote_x, quote_y + quote_height + 4)
        self.set_y(quote_y + 2)
        self.set_font('Times', 'I', 11)
        self.set_text_color(*COLOR_PALETTE["text_light"])
        self.multi_cell(0, 6, text, 0, 'L')
        self.set_left_margin(self.l_margin)
        self.ln(6)


def parse_summary_file(filepath):
    """Parses a text file with simple markdown-like syntax."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    article_data = {"title": "Untitled Article", "subtitle": "", "content": []}
    processing_lines = list(lines)
    title_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith('# ') and not title_found:
            article_data["title"] = line.lstrip('# ').strip()
            processing_lines.pop(i)
            title_found = True
            break

    paragraph_buffer = []
    for line in processing_lines:
        line = line.strip()
        if not line:
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            continue

        if line.startswith('## '):
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("header", line.lstrip('## ').strip()))
        elif line.startswith('### '):
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("subheader", line.lstrip('### ').strip()))
        elif line.startswith('* '):
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("bullet", line.lstrip('* ').strip()))
        elif line.startswith('> '):
            if paragraph_buffer:
                article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
                paragraph_buffer = []
            article_data["content"].append(("quote", line.lstrip('> ').strip()))
        else:
            paragraph_buffer.append(line)

    if paragraph_buffer:
        article_data["content"].append(("paragraph", " ".join(paragraph_buffer)))
    return article_data


def create_article_pdf(article_data, filename="magazine_article.pdf"):
    """Generates the PDF file from the parsed article data."""

    def sanitize_text(text):
        """Replaces common unsupported Unicode characters with safe equivalents."""
        unicode_map = {
            u"\u2018": "'", u"\u2019": "'", u"\u201c": '"', u"\u201d": '"',
            u"\u2014": "--", u"\u2026": "..."
        }
        for unicode_char, safe_char in unicode_map.items():
            text = text.replace(unicode_char, safe_char)
        # Encode to the standard PDF font encoding, replacing any other unsupported characters
        return text.encode("cp1252", "replace").decode("cp1252")

    pdf = PDF('P', 'mm', 'A4')
    pdf.set_article_meta(sanitize_text(article_data["title"]), sanitize_text(article_data["subtitle"]))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    first_heading = True
    for content_type, text in article_data["content"]:
        sanitized_text = sanitize_text(text)
        if content_type == "header":
            if not first_heading:
                pdf.draw_section_separator()
            pdf.show_heading(sanitized_text)
            first_heading = False
        elif content_type == "subheader":
            pdf.ln(4)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*COLOR_PALETTE["text_dark"])
            pdf.multi_cell(0, 7, sanitized_text, 0, 'L')
            pdf.ln(2)
        elif content_type == "paragraph":
            pdf.show_paragraph(sanitized_text)
        elif content_type == "bullet":
            pdf.show_bullet_point(sanitized_text)
        elif content_type == "quote":
            pdf.show_quote(sanitized_text)

    try:
        pdf.output(filename)
        print(f"Successfully created beautiful magazine article: {filename}")
    except Exception as e:
        print(f"An error occurred while creating the PDF: {e}")


if __name__ == '__main__':
    raw_summaries_dir = "raw_summaries"
    if not os.path.exists(raw_summaries_dir):
        print(f"Error: Directory '{raw_summaries_dir}' not found.")
        exit()

    summaries_dir = 'gemini_pdf_summaries'
    if not os.path.exists(summaries_dir):
        os.makedirs(summaries_dir)

    for filename in os.listdir(raw_summaries_dir):
        if filename.endswith(".txt"):
            input_file = os.path.join(raw_summaries_dir, filename)
            output_filename = os.path.splitext(filename)[0] + ".pdf"
            parsed_data = parse_summary_file(input_file)
            create_article_pdf(parsed_data, filename=os.path.join(summaries_dir, output_filename))