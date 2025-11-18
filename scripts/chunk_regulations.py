"""
Script to chunk EU regulation PDFs into structured text chunks.
"""
import os
import re
import json
import sys
import logging
from pathlib import Path
from tqdm import tqdm
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import REGULATIONS_DIR, CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Extracted text content
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    # Basic cleanup
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def chunk_eu_law(text: str, doc_title: str) -> list:
    """
    Chunk EU regulations/directives by recitals and articles.
    
    Args:
        text: Full text of the regulation
        doc_title: Title of the document
    
    Returns:
        List of chunk dictionaries
    """
    chunks = []

    # Split recitals
    recitals = re.findall(r"\(\d+\).*?(?=\(\d+\)|HAVE ADOPTED|TITLE I|Article\s+1)", text, re.S)
    for r in recitals:
        num = re.match(r"\((\d+)\)", r)
        if num:
            chunks.append({
                "section": "Recital",
                "number": int(num.group(1)),
                "text": r.strip(),
                "document_title": doc_title
            })

    # Split articles
    article_blocks = re.split(r"(?=Article\s+\d+)", text)
    for art in article_blocks:
        match = re.match(r"Article\s+(\d+)", art)
        if match:
            art_num = int(match.group(1))
            chunks.append({
                "section": "Article",
                "article_number": art_num,
                "text": art.strip(),
                "document_title": doc_title
            })

    # Fallback chunking for very long texts
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    final_chunks = []
    for c in chunks:
        smalls = splitter.split_text(c["text"])
        for i, s in enumerate(smalls):
            meta = c.copy()
            meta["chunk_id"] = f"{c.get('section')}_{c.get('number', c.get('article_number', 'x'))}_{i}"
            meta["text"] = s
            final_chunks.append(meta)

    return final_chunks


def process_all_pdfs(pdf_dir: Path) -> list:
    """
    Process all PDFs in a folder and return chunks.
    
    Args:
        pdf_dir: Directory containing PDF files
    
    Returns:
        List of all chunks from all PDFs
    """
    all_chunks = []
    pdf_dir = Path(pdf_dir)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        return all_chunks
    
    for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
        logger.info(f"Processing {pdf_path.name}...")
        try:
            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_eu_law(text, pdf_path.stem)
            all_chunks.extend(chunks)
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
    
    return all_chunks


def main():
    """Main function to process regulations and save chunks."""
    logger.info("Starting regulation chunking process")
    logger.info(f"Source directory: {REGULATIONS_DIR}")
    logger.info(f"Output file: {CHUNKS_FILE}")
    
    all_chunks = process_all_pdfs(REGULATIONS_DIR)
    
    logger.info(f"Total chunks created: {len(all_chunks)}")
    
    # Save as JSONL
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for c in all_chunks:
            json.dump(c, f, ensure_ascii=False)
            f.write("\n")
    
    logger.info(f"Chunks saved to {CHUNKS_FILE}")


if __name__ == "__main__":
    main()

