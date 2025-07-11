import os
import time
import openai
from fpdf import FPDF
from tqdm import tqdm
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration
INPUT_FOLDER = "../books/"
OUTPUT_FOLDER = "gemini_pdf_summaries/"
ASSISTANT_NAME = "Book Summarizer Assistant"
MODEL = "gpt-4o"


# Create Assistant (only once)
def create_or_get_assistant():
    assistants = openai.beta.assistants.list(limit=20)
    for assistant in assistants.data:
        if assistant.name == ASSISTANT_NAME:
            return assistant.id

    print("Creating new assistant...")
    assistant = openai.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=(
            "You are a helpful book summarizer. Your job is to read uploaded PDFs of books "
            "and summarize them into engaging blog-style reviews of around 4 A4 pages. "
            "Your gemini_pdf_summaries should help readers decide whether to read the full book."
        ),
        model=MODEL,
        tools=[{"type": "file_search"}],
    )
    return assistant.id


def upload_pdf_to_openai(filepath):
    with open(filepath, "rb") as f:
        file = openai.files.create(file=f, purpose="assistants")
    return file.id


def summarize_book(assistant_id, file_id, book_title):
    print(f"📩 Creating thread for: {book_title}")
    thread = openai.beta.threads.create()

    # Send a message with no file
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Please summarize the uploaded book '{book_title}' into a ~4 A4 page summary and blog-style review.",
    )

    # Create a run with the file attached here
    run = openai.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant_id, file_ids=[file_id]
    )

    # Poll until the run is complete
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )
        if run_status.status in ["completed", "failed"]:
            break
        time.sleep(3)

    if run_status.status == "completed":
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return msg.content[0].text.value
    else:
        raise RuntimeError("Assistant failed to complete the run.")


def save_as_pdf(text, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    text = "".join([c if ord(c) < 128 else "" for c in text])  # Remove emojis

    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    assistant_id = create_or_get_assistant()

    for filename in tqdm(os.listdir(INPUT_FOLDER)):
        if filename.lower().endswith(".pdf"):
            book_path = os.path.join(INPUT_FOLDER, filename)
            book_title = os.path.splitext(filename)[0]
            print(f"\n📘 Processing: {book_title}")

            try:
                file_id = upload_pdf_to_openai(book_path)
                summary = summarize_book(assistant_id, file_id, book_title)
                output_path = os.path.join(OUTPUT_FOLDER, f"{book_title}_summary.pdf")
                save_as_pdf(summary, output_path)
                print(f"✅ Summary saved to: {output_path}")
            except Exception as e:
                print(f"❌ Failed to summarize {book_title}: {e}")


if __name__ == "__main__":
    main()
