import os
import openai
import fitz  # PyMuPDF
from fpdf import FPDF
from tqdm import tqdm
from dotenv import load_dotenv

# Load API key from environment variable
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration
INPUT_FOLDER = "books/"
OUTPUT_FOLDER = "summaries/"
MODEL = "gpt-4"  # or "gpt-3.5-turbo"


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:12000]  # Limit text length for token budget


def summarize_with_chatgpt(book_text, book_title):
    system_prompt = (
        "You are a professional book summarizer and blog writer. "
        "Summarize the following book into about 4 A4 pages. "
        "Make it useful as both a summary and an engaging blog-style review. "
        "Include key insights, structure, and tone."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Title: {book_title}\n\nBook content:\n{book_text}"}
    ]

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']


def save_as_pdf(text, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    text = ''.join([c if ord(c) < 128 else '' for c in text])  # Strip emojis

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)


def summarise_ebooks():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for filename in tqdm(os.listdir(INPUT_FOLDER)):
        if filename.lower().endswith(".pdf"):
            book_path = os.path.join(INPUT_FOLDER, filename)
            book_title = os.path.splitext(filename)[0]
            print(f"\n🔍 Processing: {book_title}")

            try:
                book_text = extract_text_from_pdf(book_path)
                summary = summarize_with_chatgpt(book_text, book_title)
                output_pdf = os.path.join(OUTPUT_FOLDER, f"{book_title}_summary.pdf")
                save_as_pdf(summary, output_pdf)
                print(f"✅ Saved summary to {output_pdf}")
            except Exception as e:
                print(f"❌ Failed to process {book_title}: {e}")


if __name__ == "__main__":
    summarise_ebooks()
