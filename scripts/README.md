# Scripts Directory

This directory contains utility scripts for data processing and setup.

## Scripts

### `chunk_regulations.py`
Processes EU regulation PDFs and creates structured text chunks.

**Usage:**
```bash
python scripts/chunk_regulations.py
```

**What it does:**
- Extracts text from PDFs in `regulations_texts/`
- Chunks text by recitals and articles
- Saves chunks to `eu_laws_chunks.jsonl`

### `create_vectorstore.py`
Creates the Chroma vector store from chunked regulations.

**Usage:**
```bash
python scripts/create_vectorstore.py
```

**What it does:**
- Loads chunks from `eu_laws_chunks.jsonl`
- Creates embeddings using OpenAI
- Builds and persists Chroma vector store in `chroma_eu_laws/`

## Setup Workflow

1. **First time setup:**
   ```bash
   # Step 1: Chunk the regulations
   python scripts/chunk_regulations.py
   
   # Step 2: Create the vector store
   python scripts/create_vectorstore.py
   ```

2. **Run the application:**
   ```bash
   chainlit run app.py -w
   ```

## Requirements

- All dependencies from `requirements.txt`
- OpenAI API key set in environment
- PDF files in `regulations_texts/` directory

