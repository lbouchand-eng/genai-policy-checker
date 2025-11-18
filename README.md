# EU Policy Compliance Checker

An intelligent Regulatory Compliance Assistant that compares internal documents (policies/procedures) against public regulations (GDPR, AI Act, NIS2, etc.) and flags discrepancies with cited articles.

## Key Features

- **Document Upload & Comparison**: Upload PDF, DOCX, or TXT files to compare against EU regulations
- **Discrepancy Detection**: Automatically identifies compliance gaps and violations
- **Article Citations**: Flags discrepancies with specific regulatory article references
- **Question-Answering**: Ask legal questions about EU regulations
- **Detailed PDF Reports**: Generate comprehensive compliance reports with:
  - Identified discrepancies with regulatory violations
  - Compliance scores
  - Actionable recommendations
  - Regulatory article references

## Features

- **Document Upload & Parsing**: Support for PDF, DOCX, and TXT files
- **Retrieval-Augmented Generation (RAG)** with Chroma and OpenAI Embeddings
- **Intelligent Document Comparison**: Compares internal policies against EU regulations
- **Structured Discrepancy Extraction**: Uses data models for consistent reporting
- **Automatic PDF Report Generator**: Formatted and structured reports
- **Interactive Chatbot**: Built with Chainlit
- **Dual-level Intelligence**:
  - Short in-chat response for fast understanding
  - Full structured PDF with discrepancies, compliance score, and next steps
- **Enhanced Retrieval**: Uses more regulatory context (8 documents) for thorough document analysis

## Architecture Overview

```
User <--> Chainlit Chat UI
         ↕
ChatOpenAI (gpt-4o-mini)
         ↕
Retriever (Chroma + OpenAI embeddings)
         ↕
Pre-processed EU Regulation Texts (PDF → Chunks)
         ↕
Report Generator (Structured Data → PDF)
```

- Data: stored in `chroma_eu_laws/`
- Reports: generated dynamically on user queries
- Vector embeddings: `text-embedding-3-small`

## Installation

### 1. Clone & Setup Environment

```bash
git clone <your_repo_url>
cd genai_final_project_leo_benjo
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Add Your OpenAI API Key

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
# Then edit .env and add your OpenAI API key
```

Or create it manually:
```
OPENAI_API_KEY=sk-xxxx...
```

Alternatively, the application will prompt for the API key if not found in the environment.

### 3. Setup the Vector Database (First Time Only)

```bash
# Process regulation PDFs into chunks
python scripts/chunk_regulations.py

# Create the vector store
python scripts/create_vectorstore.py
```

### 4. Run the Application

```bash
chainlit run app.py -w
```

## How It Works

### Document Comparison Mode

1. User uploads a policy/procedure document (PDF, DOCX, or TXT)
2. The app extracts text from the document
3. Relevant EU regulations are retrieved using semantic search (ChromaDB)
4. GPT-4o-mini compares the document against regulations using structured JSON output
5. Discrepancies are identified with regulatory violations
6. A detailed PDF report is generated in the `output/` directory with:
   - List of discrepancies with regulatory violations
   - Compliance score
   - Actionable recommendations

### Question-Answering Mode

1. User enters a legal question about EU regulations
2. The app retrieves relevant EU legal texts using ChromaDB
3. GPT-4o-mini analyzes and synthesizes the legal context
4. The chatbot provides a short answer with sources

## Evaluation

A dedicated `notebooks/evaluation.ipynb` notebook is provided to:

- Test the RAG pipeline across various queries
- Compare GPT answers vs expected legal interpretations
- Store results in a CSV for performance analysis

## Project Structure

```
genai-policy-checker/
├── app.py                        # Chainlit main application
├── src/                          # Production code modules
│   ├── __init__.py
│   ├── config.py                # Centralized configuration
│   ├── rag.py                   # RAG pipeline implementation
│   ├── document_parser.py       # Document text extraction (PDF, DOCX, TXT)
│   ├── report_generator.py      # PDF report generation
│   ├── models.py                # Data models for compliance analysis
│   ├── citation_validator.py    # Citation extraction and validation
│   ├── discrepancy_parser.py   # Structured discrepancy parsing
│   └── exceptions.py            # Custom exception classes
├── scripts/                      # Utility scripts
│   ├── chunk_regulations.py     # Process PDFs into chunks
│   └── create_vectorstore.py    # Create vector database
├── data/                         # Data directory
├── output/                       # Generated compliance reports (PDFs)
├── regulations_texts/            # Source EU regulation PDFs
├── chroma_eu_laws/              # Vector database (generated)
├── eu_laws_chunks.jsonl         # Text chunks (generated)
├── chainlit.md                   # Chainlit configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── .env                         # Environment variables (not in git, create from .env.example)
```

## Example Usage

### Example 1: Document Upload

1. Upload your company's privacy policy (PDF/DOCX)
2. The system compares it against GDPR, AI Act, and other relevant regulations
3. Receive a report with:
   - **Discrepancy 1**: Missing data retention period
     - **Regulatory Violation**: GDPR Article 5(1)(e)
     - **Required Action**: Specify retention periods for each data category

### Example 2: Question-Answering

**Question:**
> Can I store photos of employees for internal authentication?

**Chat Answer:**
> Yes, you can store photos of employees for internal authentication under GDPR, but you must adhere to specific legal requirements: ...

The answer includes sources from the retrieved regulatory documents.

## Technologies

| Component | Library |
|-----------|---------|
| Vector DB | Chroma |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | ChatOpenAI (gpt-4o-mini) |
| Interface | Chainlit |
| PDF Generator | ReportLab |
| Document Parser | PyPDF2, python-docx |
| Data | Official EU Regulation Texts (GDPR, AI Act, etc.) |

## Implemented Features

- Document upload for company policies (PDF, DOCX, TXT)
- Automatic discrepancy detection
- Regulatory violation identification in discrepancy reports
- Structured discrepancy data models
- Enhanced retrieval for document comparison
- Professional logging and error handling
- Structured JSON output from LLM

## Future Improvements

- Add multilingual support (FR/EN)
- Add database of local EU Data Protection Authorities
- Fine-tune model on compliance language
- Support for batch document processing
- Integration with document management systems
- Enhanced citation matching algorithms

## Authors

Léo Bouchand, Benjamin Rasson

Academic Project — Applied AI & Data Science 2025
