import os
import fitz  # PyMuPDF
import jsonlines
from generate_QAdataset import generate_qa_ollama  # Adjust this import!
import tkinter as tk
from tkinter import filedialog
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --------------------------
# PDF Text Extraction
# --------------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# --------------------------
# Basic Chunking by Paragraphs or Tokens
# --------------------------
def simple_chunk_text(text, max_words=30):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i + max_words]))
    return chunks

# --------------------------
# Main Script
# --------------------------
def main():
    # Open file dialog to select a PDF
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    pdf_paths = filedialog.askopenfilenames(
        title="Select PDF files",
        filetypes=[("PDF files", "*.pdf")]
    )
    if not pdf_paths:
        print("No file selected.")
        return

    output_file = "qa_dataset.jsonl"
    role = "general_access for any role employee"  # or manager, hr, etc

    dataset = []

    for pdf_path in pdf_paths:
        print(f"Processing: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,  # More reasonable for QA
            chunk_overlap=20
        )
        chunks = splitter.split_text(text)
        print(f"  Extracted {len(chunks)} chunks.")

        # Generate QA pairs for each chunk
        # Limit to first 10 chunks for testing
        for i, chunk in enumerate(chunks[:10]):  # Limit for faster testing; remove [:10] in final run
            print(f"    Generating QA for chunk {i+1}/{min(10, len(chunks))}")
            qa = generate_qa_ollama(chunk, role=role)
            if qa:
                # Optionally, add PDF filename to each QA for traceability
                qa["source_pdf"] = os.path.basename(pdf_path)
                dataset.append(qa)
            else:
                print(f"    Failed to generate QA for chunk {i+1}")

    if not dataset:
        print("No QA pairs generated. Please check your PDFs or QA generation function.")
        return

    # Save to JSONL
    with jsonlines.open(output_file, mode="a") as writer:
        for item in dataset:
            writer.write(item)

    print(f"\n✅ Saved {len(dataset)} QA pairs to {output_file}")

if __name__ == "__main__":
    main()
