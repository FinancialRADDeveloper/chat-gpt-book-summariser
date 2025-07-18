# AI Book Summariser

A comprehensive tool for generating and formatting book summaries using various AI models including Claude, Gemini, and ChatGPT.

## Project Overview

This project provides tools to:

1. **Generate book summaries** using Google's Gemini Vision API by analyzing PDF books
2. **Convert raw text summaries** into professionally formatted PDFs with custom styling
3. Support for multiple AI models:
   - **Claude**: Convert Claude-generated summaries to PDFs with Nord color scheme
   - **Gemini**: Generate summaries from PDFs and convert to professionally styled PDFs
   - **ChatGPT**: Support for processing ChatGPT-generated summaries

## Setup Instructions

### 1. Create Conda Environment

```bash
conda create -n book-summariser python=3.13
conda activate book-summariser
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. API Keys Setup

For Gemini functionality, create a `.env` file in the project root with your API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage Instructions

### Converting Raw Summaries to PDFs (Claude)

1. Place your raw text summaries in the `raw_summaries` folder with `.txt` extension
2. Run the conversion script:

```bash
python src/raw_summary_to_pdf_claude.py --folder
```

This will process all text files in the `raw_summaries` folder and output PDFs to the `claude_pdf_summaries` folder.

For a single file:

```bash
python src/raw_summary_to_pdf_claude.py input_file.txt output_file.pdf
```

### High Contrast Version (Claude)

For a high contrast version of the Claude PDF output:

```bash
python src/raw_summary_to_pdf_claude_high_contrast.py --folder
```

### Generating Summaries with Gemini Vision

To generate summaries from PDF books using Gemini:

1. Place your PDF books in the `books` folder
2. Run the Gemini summarizer:

```bash
python src/gemini_book_summariser.py
```

This will:
- Upload each PDF to Gemini's Files API
- Generate a comprehensive summary and review
- Create a professionally formatted PDF in the `gemini_pdf_summaries` folder

## Directory Structure

- `books/`: Place PDF books here for Gemini to analyze
  - `processed/`: Processed books are moved here
  - `xlarge/`: For extra large books
- `src/`: Source code
  - `raw_summaries/`: Place raw text summaries here
  - `claude_pdf_summaries/`: Output folder for Claude-formatted PDFs
  - `claude_pdf_summaries_high_contrast/`: Output folder for high-contrast Claude PDFs
  - `gemini_pdf_summaries/`: Output folder for Gemini-generated summaries

## Dependencies

- **AI APIs**:
  - `google.generativeai`: For Gemini Vision API
  - `openai`: For ChatGPT API
  
- **PDF Processing**:
  - `reportlab`: For creating formatted PDFs
  - `fpdf`: Alternative PDF generator
  - `fitz` (PyMuPDF): For processing/reading PDFs
  
- **Text Processing**:
  - `markdown`: For parsing markdown text
  - `beautifulsoup4`: For HTML/XML parsing
  
- **Utilities**:
  - `python-dotenv`: For loading environment variables
  - `tqdm`: For progress bars

## Updating Requirements

To update the requirements.txt file:

```bash
pip install pipreqs
pipreqs ./ --force
```

## Contributing

Feel free to submit issues or pull requests to improve the functionality or add support for additional AI models.

## License

This project is available for personal and educational use.