import os
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from dotenv import load_dotenv
import time  # Import time for sleep
import sys

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

            Your output should be structured to fill approximately 4 pages when formatted, comprising:

            **Pages 1-3: Comprehensive Summary**
            * Thoroughly explain the book's main arguments, core concepts, and key takeaways.
            * Break down complex ideas into clear, concise language suitable for a busy tech executive.
            * Adopt an engaging, analytical, and insightful tone.
            * Focus on the most valuable and relevant information for professionals in the technology sector.
            * Organize the summary into logical sections (e.g., "Introduction to [Key Theme]," "Core Principles of [Author's Approach]," "Practical Applications for Tech Leaders," "Case Studies/Examples"). Aim for depth while maintaining conciseness to fit within 3 pages.

            **Page 4: Review and Recommendation**
            * Provide a professional yet entertaining review.
            * Evaluate the book's worthiness for your audience. Justify your assessment based on:
                * The originality of its ideas and perspectives.
                * The presence of actionable insights that tech leaders can immediately apply.
                * Its relevance to current and emerging technology trends.
                * The clarity, depth, and persuasiveness of the author's writing style.
                * Any notable strengths or weaknesses (e.g., areas where it excels or falls short).
                * Clearly define the ideal target audience for this book (e.g., "Essential for CTOs focusing on AI strategy," "A must-read for product managers in disruptive startups," "Beneficial for anyone exploring the intersection of X and Y")).
            * Conclude with a definitive recommendation (e.g., "Highly recommended," "Worth a read," "For specific audiences only").

            Maintain a consistent voice: insightful, authoritative, and engaging. Prioritize clarity over jargon, but embrace technical detail where it adds value.
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

            # --- Build the Story ---
            story.append(Paragraph(f"Book Summary & Review: {book_title}", styles['h1']))
            story.append(Paragraph("A Professional Review for Tech Leaders", styles['h2']))
            story.append(Spacer(1, 0.4 * inch))

            # Parse and add the AI-generated text using the new styles.
            for para_text in summary_and_review_text.split('\n'):
                if not para_text.strip():
                    continue  # Skip empty lines

                if para_text.startswith('## '):
                    story.append(Paragraph(para_text.lstrip('## ').strip(), styles['h3']))
                elif para_text.startswith('> '):
                    story.append(Paragraph(para_text.lstrip('> ').strip(), styles['Quote']))
                    # Add extra space after a quote to let it stand out
                    story.append(Spacer(1, 0.1 * inch))
                elif para_text.startswith('* '):
                    story.append(Paragraph(para_text.lstrip('* ').strip(), styles['Bullet'], bulletText='•'))
                else:
                    story.append(Paragraph(para_text, styles['Normal']))

            doc.build(story)
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
