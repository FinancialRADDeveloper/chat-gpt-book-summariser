import os
import openai
import fitz  # PyMuPDF
from fpdf import FPDF
from tqdm import tqdm

# Set your OpenAI API key
openai.api_key = "your_openai_api_key_here"

# Configuration
input_folder = "books/"
output_folder = "summaries/"
model = "gpt-4"  # or gpt-3.5-turbo for cheaper/faster

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:12000]  # Limit to fit within GPT-4 token limits


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
        model=model,
        messages=messages,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']


def save_as_pdf(text, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Remove emojis/special characters
    text = ''.join([c if ord(c) < 128 else '' for c in text])

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)


# Batch process all PDFs
for filename in tqdm(os.listdir(input_folder)):
    if filename.lower().endswith(".pdf"):
        book_path = os.path.join(input_folder, filename)
        book_title = os.path.splitext(filename)[0]
        text = extract_text_from_pdf(book_path)

        print(f"Summarizing: {book_title}")
        try:
            summary = summarize_with_chatgpt(text, book_title)
            output_path = os.path.join(output_folder, f"{book_title}_summary.pdf")
            save_as_pdf(summary, output_path)
        except Exception as e:
            print(f"Failed to process {book_title}: {e}")
