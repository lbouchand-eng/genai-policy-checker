"""
Script to create the Chroma vector store from chunked regulations.

Extracted from embedding_and_vector.ipynb for production use.
"""
import os
import json
import sys
import logging
from pathlib import Path
from getpass import getpass
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import CHUNKS_FILE, CHROMA_DIR, EMBED_MODEL

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") \
    or getpass("Enter your OpenAI API key: ")


def load_chunks(chunks_file: Path) -> list:
    """
    Load chunks from JSONL file.
    
    Args:
        chunks_file: Path to JSONL file containing chunks
    
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    chunks_path = Path(chunks_file)
    
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_file}")
    
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    
    return chunks


def create_documents(chunks: list) -> list:
    """
    Convert chunk dictionaries to LangChain Documents.
    
    Args:
        chunks: List of chunk dictionaries
    
    Returns:
        List of LangChain Document objects
    """
    docs = [
        Document(
            page_content=c["text"],
            metadata={
                "source": c["document_title"],
                "section": c.get("section"),
                "article": c.get("article_number"),
                "recital": c.get("number")
            }
        )
        for c in chunks
    ]
    return docs


def create_vectorstore(chunks_file: Path, chroma_dir: Path, embed_model: str = EMBED_MODEL) -> Chroma:
    """
    Create and persist a Chroma vector store from chunks.
    
    Args:
        chunks_file: Path to JSONL file containing chunks
        chroma_dir: Directory to save the vector store
        embed_model: Embedding model name
    
    Returns:
        The created Chroma vectorstore
    """
    logger.info(f"Loading chunks from {chunks_file}")
    chunks = load_chunks(chunks_file)
    logger.info(f"Loaded {len(chunks)} chunks")
    
    logger.info("Converting to LangChain Documents")
    docs = create_documents(chunks)
    logger.info(f"Created {len(docs)} documents")
    
    logger.info(f"Creating embeddings with {embed_model}")
    embeddings = OpenAIEmbeddings(model=embed_model)
    
    logger.info(f"Creating vector store in {chroma_dir}")
    vectorstore = Chroma.from_documents(
        docs, 
        embeddings, 
        persist_directory=str(chroma_dir)
    )
    
    logger.info(f"Vector store created and saved in {chroma_dir}")
    return vectorstore


def main():
    """Main function to create the vector store."""
    logger.info("Starting vector store creation")
    logger.info(f"Chunks file: {CHUNKS_FILE}")
    logger.info(f"Vector store directory: {CHROMA_DIR}")
    
    try:
        vectorstore = create_vectorstore(CHUNKS_FILE, CHROMA_DIR)
        logger.info("Vector store creation complete")
        
        # Verify the vector store
        retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
        test_docs = retriever.invoke("GDPR")
        logger.info(f"Verification: Retrieved {len(test_docs)} test document(s)")
        
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        raise


if __name__ == "__main__":
    main()

