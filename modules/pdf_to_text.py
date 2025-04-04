import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def clean_pdf_text(raw_text: str) -> str:
    # Step 1: Strip unnecessary formating and lines
    # PDFs often come with broken lines and odd spacing
    # Split raw PDF text into lines and remove blank ones
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Loop over the lines to decide what is useful and what is unnecessary
    cleaned_lines = []
    for line in lines:
        # PDFs often have footers/headers like 1 | Page, 1 | P a g e, Page 1
        # These repeat on every page but contain no useful content
        # Remove any short line that contains 'page'
        # \b = word boundary (ensures matches are 'page' not 'pager', etc)
        # \s* = optional spaces
        if re.search(r"\bp\s*a\s*g\s*e\b", line, re.IGNORECASE) and len(line.split()) <= 5:
            continue

        # Remove lines starting with common headings (Name, Date, etc.)
        if re.match(r"^(Name|Date|Class|Section)\s*[:\-]", line, re.IGNORECASE):
            continue

        cleaned_lines.append(line)

    # Step 2: Re-join lines into a full block of text
    joined = " ".join(cleaned_lines)

    # Step 3: Fix common OCR issues (double spaces, hyphenated line breaks, etc.)
    # Join hyphenated words back together which might have been split due to formatting in the PDF such as...
    # binary num-
    # ber
    joined = re.sub(r"-\s+", "", joined)
    # Normalise whitespace because sometimes PDF extraction adds extra spaces (e.g. between words or after punctuation)
    # This reduces multiple spaces to a single space
    joined = re.sub(r"\s{2,}", " ", joined)
    # Remove space before punctuation to fix things such as "binary , logical shift ." to become "binary, logical shift."
    joined = re.sub(r"\s+([.,!?;:])", r"\1", joined)

    return joined.strip()

# Testing
pdf_text = extract_text_from_pdf("../example_homework.pdf")
cleaned = clean_pdf_text(pdf_text)
print(cleaned)
