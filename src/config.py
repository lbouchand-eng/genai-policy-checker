"""
Configuration settings for the EU Policy Compliance Checker.
"""
import os
import logging
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
REGULATIONS_DIR = PROJECT_ROOT / "regulations_texts"
CHROMA_DIR = PROJECT_ROOT / "chroma_eu_laws"
CHUNKS_FILE = PROJECT_ROOT / "eu_laws_chunks.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Model configuration
EMBED_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0

# RAG configuration
RETRIEVER_K = 4
DOCUMENT_RETRIEVER_K = 8

# Chunking configuration
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 300

# Document processing limits
MAX_DOCUMENT_LENGTH = 50000
RETRIEVAL_QUERY_LENGTH = 2000
ANALYSIS_DOCUMENT_LENGTH = 10000

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REGULATIONS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT
)

