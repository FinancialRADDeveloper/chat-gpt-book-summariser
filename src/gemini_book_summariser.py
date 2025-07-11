import os
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import Flowable
from dotenv import load_dotenv
import time  # Import time for sleep
import sys
import re

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Ensure these paths are correct relative to where you run the script,
# or provide absolute paths.
PDF_FOLDER = "../books"  # Adjust if your 'books' folder is elsewhere
OUTPUT_FOLDER = "summaries"  # This will create a 'summaries' folder in the script's directory
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a model that supports multimodal input (like Gemini 1.5 Pro)
# 'gemini-1.5-pro-latest' is the correct and most capable model for this task.
MODEL_NAME = 'gemini-1.5-flash-latest'


# --- Custom Flowables ---
class HorizontalLine(Flowable):
    """A horizontal line with thickness and color."""
    def __init__(self, width, thickness=1, color=None):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color

    def draw(self):
        if self.color:
            self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

    class FancySectionHeader(Flowable):
    """A fancy section header with background."""
    def __init__(self, text, width, height=0.3*inch, font_name='Helvetica-Bold', font_size=14, 
                 bg_color=None, text_color=None):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height
        self.font_name = font_name
        self.font_size = font_size
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self):
        # Draw background
        if self.bg_color:
            self.canv.setFillColor(self.bg_color)
            self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Draw text
        self.canv.setFont(self.font_name, self.font_size)
        if self.text_color:
            self.canv.setFillColor(self.text_color)
        text_width = self.canv.stringWidth(self.text, self.font_name, self.font_size)
        y_position = (self.height - self.font_size) / 2
        self.canv.drawString(10, y_position, self.text)

# --- Main Processing Logic ---
def process_ebooks_with_gemini_vision():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output folder: {OUTPUT_FOLDER}")

    # Check if PDF_FOLDER exists and contains files
    if not os.path.exists(PDF_FOLDER):
        print(f"Error: PDF_FOLDER '{PDF_FOLDER}' does not exist.")
        return

    pdf_files_found = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    if not pdf_files_found:
        print(f"No PDF files found in '{PDF_FOLDER}'. Please ensure there are PDFs in that directory.")
        return

    for filename in pdf_files_found:
        pdf_path = os.path.join(PDF_FOLDER, filename)
        book_title = os.path.splitext(filename)[0]
        print(f"\n--- Processing: {book_title} ---")

        uploaded_file_obj = None  # Initialize to None for cleanup in finally block
        try:
            # 1. Upload PDF to Gemini Files API
            print(f"Uploading '{book_title}' (from {pdf_path}) to Gemini Files API...")

            # The genai.upload_file function returns a google.generativeai.types.File object.
            # This File object itself can be directly passed as a content part to the model.
            uploaded_file_obj = genai.upload_file(path=pdf_path, display_name=filename)

            # Wait for the file to be processed
            print(f"Waiting for '{book_title}' (file name: {uploaded_file_obj.name}) to be processed by Gemini...")

            # Use uploaded_file_obj.state.name directly for state checking
            while uploaded_file_obj.state.name == 'PROCESSING':
                time.sleep(5)
                # Re-fetch the file state
                uploaded_file_obj = genai.get_file(uploaded_file_obj.name)

            if uploaded_file_obj.state.name != 'ACTIVE':
                print(
                    f"Error processing '{book_title}' via Files API. State: {uploaded_file_obj.state.name}. Skipping.")
                continue  # Skip to the next file

            print(f"Successfully uploaded '{book_title}'. Gemini File URI: {uploaded_file_obj.uri}")

            # 2. Generate Summary and Review using Gemini
            final_prompt = f"""
            You are a highly respected technology thought leader, writing a professional yet entertaining review and summary for your blog/LinkedIn.
            The book provided is titled: "{book_title}".

            Your output should be structured as a professionally formatted blog post with clear headings, comprising:

            # BOOK SUMMARY: {book_title}

            ## Introduction
            * Begin with a brief overview of the book, its author, and why it matters in today's tech landscape.
            * Include the book's core premise and promise to readers in 2-3 sentences.
            * Mention why you decided to review this particular book.

            ## Key Concepts and Insights
            * Break down 3-5 major concepts from the book using clear ### subheadings for each concept.
            * Thoroughly explain these ideas with examples from the book.
            * Use bullet points for listing important elements.
            * Include relevant quotes from the book using > quote format.

            ## Practical Applications
            * Discuss how tech leaders can apply these concepts in their work.
            * Provide specific scenarios or examples of practical implementation.
            * Include actionable steps or frameworks the book provides.

            ## Critical Analysis
            * What does the book do exceptionally well?
            * Where could it have been improved or gone deeper?
            * How does it compare to other works in this domain?

            # FINAL REVIEW AND RECOMMENDATION
            * Provide your overall assessment of the book's value to tech leaders.
            * Evaluate based on: originality, actionable insights, relevance to current tech trends, and writing quality.
            * Clearly define the ideal reader profile for this book.
            * End with a definitive verdict (e.g., "Highly recommended," "Worth a read," "For specific audiences only").

            Format your response using Markdown:
            - Use # for main sections, ## for subsections, and ### for topics
            - Use * or - for bullet points
            - Use > for notable quotes
            - Use **bold** for emphasis on important points
            - Break text into concise, readable paragraphs

            Make it engaging, insightful, and valuable for busy tech executives who want to know if this book is worth their time.
            """

            print(f"Sending prompt and uploaded PDF for '{book_title}' to Gemini model '{MODEL_NAME}'...")
            model = genai.GenerativeModel(MODEL_NAME)

            # Use stream=True to get the response as an iterator.
            response = model.generate_content(
                [uploaded_file_obj, final_prompt],
                stream=True
            )

            # Create a variable to hold the complete text and print the stream.
            summary_and_review_text = ""
            print("\n--- Gemini Response Stream ---")
            for chunk in response:
                # Print each chunk to the console as it arrives.
                # The `end=""` and `flush=True` arguments ensure the text
                # appears on the same line without waiting.
                print(chunk.text, end="", flush=True)

                # Append the chunk's text to our full response string.
                summary_and_review_text += chunk.text

            # Print a newline to clean up the console output after the stream finishes.
            print("\n--- End of Stream ---\n")

            print(f"Generated summary and review for '{book_title}'.")

            # 3. Create Formatted PDF with Advanced Styling
            output_pdf_path = os.path.join(OUTPUT_FOLDER, f"{book_title}_Summary_Review.pdf")
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, topMargin=inch, bottomMargin=inch,
                                    leftMargin=inch, rightMargin=inch)

            # --- Custom Styles ---
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib import colors

            # Define custom colors for a professional look
            dark_grey = colors.HexColor("#2C3E50")
            light_grey = colors.HexColor("#7F8C8D")
            accent_blue = colors.HexColor("#3498DB")
            quote_bg_color = colors.HexColor("#ECF0F1")  # A light background for quotes

            styles = {
                'h1': ParagraphStyle(name='h1', fontName='Helvetica-Bold', fontSize=24, textColor=dark_grey,
                                     spaceAfter=18, leading=30),
                'h2': ParagraphStyle(name='h2', fontName='Helvetica', fontSize=16, textColor=light_grey, spaceAfter=12,
                                     leading=20),
                'h3': ParagraphStyle(name='h3', fontName='Helvetica-Bold', fontSize=14, textColor=accent_blue,
                                     spaceBefore=12, spaceAfter=6, leading=18),
                'Normal': ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=11, textColor=dark_grey,
                                         spaceAfter=6, leading=16, alignment=4),  # Justified
                'Bullet': ParagraphStyle(name='Bullet', fontName='Helvetica', fontSize=11, textColor=dark_grey,
                                         spaceAfter=4, leading=16, leftIndent=18, bulletIndent=0),
                'Quote': ParagraphStyle(name='Quote', fontName='Helvetica-Oblique', fontSize=11,
                                        textColor=colors.HexColor("#2C3E50"), spaceBefore=10, spaceAfter=10, leading=16,
                                        leftIndent=15, rightIndent=15, backColor=quote_bg_color, borderPadding=10,
                                        borderColor=accent_blue, borderWidth=1)
            }
            story = []

            # --- Extract sections and create TOC ---
            # First pass: Extract headings and structure
            sections = []
            current_section = ""
            section_pattern = re.compile(r'^#+\s+(.+)$|^(.+)\n[=\-]+$')  # Markdown headings

            # Process the text to extract headings
            for line in summary_and_review_text.split('\n'):
                match = section_pattern.match(line)
                if match:
                    heading = match.group(1) or match.group(2)
                    sections.append(heading.strip())

            # --- Build Cover Page ---
            # Add a professional cover page
            story.append(Paragraph(f"Book Summary & Review", styles['cover_title']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(HorizontalLine(450, 2, accent_blue))
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph(f"{book_title}", styles['cover_title']))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("A Professional Analysis for Technology Leaders", styles['cover_subtitle']))
            story.append(Spacer(1, 0.5 * inch))

            # Add a decorative element to the cover
            d = Drawing(400, 100)
            line = Line(0, 50, 400, 50, strokeWidth=1, strokeColor=accent_blue)
            d.add(line)

            # Create a pie chart showing value distribution (for visual appeal)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            pie.data = [35, 25, 20, 15, 5]  # Represent book value distribution
            pie.labels = ['Key Insights', 'Practical Tips', 'Case Studies', 'Frameworks', 'Other']
            pie.slices.strokeWidth = 0.5
            pie.slices[0].fillColor = accent_blue
            pie.slices[1].fillColor = brand_blue
            pie.slices[2].fillColor = highlight_orange
            pie.slices[3].fillColor = light_grey
            pie.slices[4].fillColor = dark_grey
            d.add(pie)

            story.append(d)
            story.append(Spacer(1, 0.3 * inch))

            # Add author info section
            story.append(Paragraph("Prepared by", styles['NormalLeft']))
            story.append(Paragraph("Professional Book Summary Service", styles['Strong']))
            story.append(Paragraph(f"Completed on: {time.strftime('%B %d, %Y')}", styles['NormalLeft']))

            # Add page break after cover
            story.append(PageBreak())

            # --- Add Table of Contents ---
            story.append(Paragraph("Table of Contents", styles['toc_title']))
            story.append(Spacer(1, 0.2 * inch))

            # Create a simple TOC manually
            toc_data = []
            for i, section in enumerate(sections):
                if len(section) > 60:  # Truncate long section names
                    section = section[:57] + "..."
                toc_data.append([Paragraph(section, styles['toc_heading']), Paragraph(f"Page {i+2}", styles['toc_item'])])

            if toc_data:  # Only create table if we have sections
                # Create the table with the TOC data
                toc_table = Table(toc_data, colWidths=[5*inch, 0.7*inch])
                toc_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.white),  # No visible grid
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, light_grey),  # Light separator lines
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),  # White background
                ]))
                story.append(toc_table)
            else:
                story.append(Paragraph("(Content sections will appear here)", styles['NormalLeft']))

            story.append(Spacer(1, 0.3 * inch))
            story.append(HorizontalLine(450, 1, light_grey))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("This summary provides key insights and analysis. Skip to the last page for the final review and recommendation.", styles['Emphasis']))

            # Add page break after TOC
            story.append(PageBreak())

            # Parse and add the AI-generated text using enhanced styles
            in_review_section = False
            current_heading_level = 0
            section_count = 0

            # Process the content with improved formatting
            for para_text in summary_and_review_text.split('\n'):
                if not para_text.strip():
                    continue  # Skip empty lines

                # Check for Markdown headings of different levels
                if para_text.startswith('# '):
                    section_count += 1
                    heading_text = para_text.lstrip('# ').strip()
                    # Add a page break before major sections except the first one
                    if section_count > 1:
                        story.append(PageBreak())

                    # Add fancy section header
                    story.append(FancySectionHeader(heading_text, 450, bg_color=brand_blue, text_color=colors.white))
                    story.append(Spacer(1, 0.15 * inch))

                    # Check if we're entering the review section
                    if "review" in heading_text.lower() or "recommendation" in heading_text.lower():
                        in_review_section = True

                        # Add a visual indicator for the review section
                        story.append(Paragraph("FINAL ASSESSMENT", styles['toc_title']))

                elif para_text.startswith('## '):
                    heading_text = para_text.lstrip('## ').strip()
                    story.append(Paragraph(heading_text, styles['h2']))
                    story.append(HorizontalLine(450, 1, light_grey))
                    story.append(Spacer(1, 0.1 * inch))

                elif para_text.startswith('### '):
                    story.append(Paragraph(para_text.lstrip('### ').strip(), styles['h3']))

                elif para_text.startswith('#### '):
                    story.append(Paragraph(para_text.lstrip('#### ').strip(), styles['h4']))

                elif para_text.startswith('> '):
                    # Enhanced quote styling
                    quote_text = para_text.lstrip('> ').strip()
                    story.append(Paragraph(f'"{quote_text}"', styles['Quote']))
                    story.append(Spacer(1, 0.1 * inch))

                elif para_text.startswith('* ') or para_text.startswith('- '):
                    # Enhanced bullet point styling
                    bullet_text = para_text.lstrip('*- ').strip()
                    story.append(Paragraph(bullet_text, styles['Bullet'], bulletText='•'))

                elif para_text.startswith('```') or para_text.endswith('```'):
                    # Skip code blocks or handle them if needed
                    continue

                elif in_review_section and ('recommend' in para_text.lower() or 
                                          'conclusion' in para_text.lower() or
                                          'verdict' in para_text.lower()):
                    # Highlight recommendation text
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(para_text, styles['Callout']))
                    story.append(Spacer(1, 0.2 * inch))

                else:
                    # Check for bold and italic text in paragraphs
                    if '**' in para_text or '__' in para_text:
                        # Has bold text - use strong style
                        story.append(Paragraph(para_text.replace('**', '<b>').replace('__', '<b>'), styles['Strong']))
                    elif '*' in para_text or '_' in para_text:
                        # Has italic text - use emphasis style
                        story.append(Paragraph(para_text.replace('*', '<i>').replace('_', '<i>'), styles['Emphasis']))
                    else:
                        # Regular paragraph
                        story.append(Paragraph(para_text, styles['Normal']))

            # Custom document building with footer
            def add_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 9)
                canvas.setFillColor(light_grey)
                footer_text = f"Book Summary & Review | {book_title} | Generated on {time.strftime('%B %d, %Y')}"
                canvas.drawCentredString(letter[0]/2, 0.5*inch, footer_text)
                canvas.restoreState()

            # Build the PDF with the footer function
            doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
            print(f"Created styled PDF: {output_pdf_path}")

        except Exception as e:
            print(f"An error occurred while processing '{book_title}': {e}")
            import traceback
            traceback.print_exc()  # Print full traceback for better debugging
        finally:
            # Clean up: Delete the uploaded file from Gemini's service
            if uploaded_file_obj and hasattr(uploaded_file_obj, 'name'):
                try:
                    genai.delete_file(uploaded_file_obj.name)
                    print(f"Deleted temporary Gemini file '{uploaded_file_obj.name}' for '{book_title}'.")
                except Exception as e:
                    print(f"Error deleting temporary Gemini file '{uploaded_file_obj.name}': {e}")
            else:
                print(
                    f"No Gemini file to delete for '{book_title}' (upload might have failed or object missing 'name').")


# --- Run the script ---
if __name__ == "__main__":
    print(f"Python {sys.version} on {sys.platform}")
    print(f"Current working directory: {os.getcwd()}")
    process_ebooks_with_gemini_vision()
    print("\n--- Processing Complete ---")
