#app/auto_tagging.py
from langchain_ollama import OllamaLLM as Ollama

import logging
import os
import asyncio
import fitz  # PyMuPDF
import aiohttp

logging.basicConfig(level=logging.INFO)

# Define your tag classes
ACCESS_TAGS = ["hr_only", "it_only", "finance_only", "general_access"]

# Keyword patterns for rule-based tagging
PATTERNS = {
    "hr_only": ["employee benefits", "hiring policy", "performance review", "leave policy", "payroll", "recruitment", "code of conduct", "employee handbook"],
    "it_only": ["server", "database", "API", "network", "firewall", "cybersecurity", "VPN", "infrastructure", "backend", "DevOps", "source code"],
    "finance_only": ["budget", "invoice", "financial statement", "balance sheet", "ledger", "payables", "receivables", "audit", "profit and loss", "tax"],
    "general_access": ["announcement", "notice", "schedule", "event", "update", "welcome", "guide", "handbook", "policy"]
}

# llm for fallback strategy:
llm = Ollama(
    model="mistral",
    temperature=0.3,
    max_tokens=1024
)

# prompt template
def build_llm_prompt(text: str) -> str:
    """Build prompt for LLM-based classification."""
    return f"""
You are a document content classification assistant.

Classify the document based on the following rules. Choose **only one** tag:
- "general_access": for documents suitable for all employees.
- "hr_only": for HR or employee policy-related content.
- "it_only": for IT, tech, or infrastructure-related content.
- "finance_only": for financial or accounting-related content.

If you feel the content is suitable for everyone, choose only "general_access".

Respond with just the tag string. No JSON or explanation.

Document content:
\"\"\"
{text[:3000]}
\"\"\"
"""

# Async function to call Ollama
async def call_ollama(prompt: str) -> list:
    response = await llm.ainvoke(prompt)
    try:
        tag_data = eval(response.strip())  # simple JSON-likex
        return tag_data.get("access_tags", [])
    except Exception as e:
        print("⚠️ Failed to parse tags:", response)
        return []
    

async def classify_with_llm(text:str)->str:
    """Call LLM to classify and return a single tag."""
    prompt = build_llm_prompt(text)
    response = await llm.ainvoke(prompt)
    tag = response.strip().lower()

    if tag in ACCESS_TAGS:
        return tag
    else:
        logging.warning(f"⚠️ Unexpected LLM response: {response}")
        return "general_access"  # Fallback default    

# Text extractor using PyMuPDF
def extract_pdf_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    return full_text.strip()

# extract first max_words words from the PDF
def extract_text_head(pdf_path: str, max_words: int = 100) -> str:
    """Extract first `max_words` words from the PDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + " "
        if len(text.split()) >= max_words:
            break
    return " ".join(text.split()[:max_words])

def match_by_keywords(text: str) -> str:
    """Match patterns in the first `k` words of text and return access tag."""
    text_lower = text.lower()
    match_counts = {tag: 0 for tag in ACCESS_TAGS}

    for tag, keywords in PATTERNS.items():
        for keyword in keywords:
            if keyword in text_lower:
                match_counts[tag] += 1

    # Choose tag with highest match count
    best_tag = max(match_counts, key=match_counts.get)

    if match_counts[best_tag] > 0:
        # If best tag is general_access, return only that
        return "general_access" if best_tag == "general_access" else best_tag
    else:
        return None  # No confident match

# === MAIN ASYNC FUNCTION ===
async def auto_tag_pdf(pdf_path: str) -> str:
    """Return a single access tag for the given PDF path."""
    logging.info(f"🔍 Processing: {pdf_path}")

    head_text = extract_text_head(pdf_path)
    tag = match_by_keywords(head_text)

    if tag:
        logging.info(f"✅ Rule-based tag found: {tag}")
        return tag
    else:
        logging.info("🤖 No confident keyword match, falling back to LLM...")
        full_text = extract_text_head(pdf_path)
        tag = await classify_with_llm(full_text)
        logging.info(f"✅ LLM-based tag: {tag}")
        return tag

# # Main async function
# async def auto_tag_pdfs(pdf_dir: str = "./pdfs"):
#     tagged_results = {}

#     for filename in os.listdir(pdf_dir):
#         if filename.endswith(".pdf"):
#             path = os.path.join(pdf_dir, filename)
#             print(f"🔍 Processing {filename}...")

#             text = extract_pdf_text(path)
#             prompt = build_prompt(text)
#             tags = await call_ollama(prompt)

#             tagged_results[filename] = tags
#             print(f"✅ {filename} → Tags: {tags}")

#     return tagged_results

# For standalone test
if __name__ == "__main__":
    asyncio.run(auto_tag_pdf())
