"""
RAG (Retrieval-Augmented Generation) pipeline for EU compliance checking.
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import Runnable, RunnableMap, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate

from src.config import (
    CHROMA_DIR,
    EMBED_MODEL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    RETRIEVER_K,
    DOCUMENT_RETRIEVER_K
)


def get_vectorstore() -> Chroma:
    """
    Initialize and return the Chroma vector store.
    
    Returns:
        Chroma vector store instance
    """
    embedding = OpenAIEmbeddings(model=EMBED_MODEL)
    return Chroma(persist_directory=str(CHROMA_DIR), embedding_function=embedding)


def get_retriever(k: int = RETRIEVER_K) -> BaseRetriever:
    """
    Get a retriever with specified k value.
    
    Args:
        k: Number of documents to retrieve
    
    Returns:
        BaseRetriever instance
    """
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


def get_rag_chain() -> Runnable:
    """
    Build and return the RAG chain for question answering.
    
    Returns:
        A LangChain Runnable chain that takes a question and returns an answer.
    """
    retriever = get_retriever(k=RETRIEVER_K)
    
    prompt = ChatPromptTemplate.from_template("""
You are a legal expert specialized in European and GDPR law.

Use the following retrieved context to answer the user's question precisely.
If uncertain, say you don't know.

Context:
{context}

Question:
{question}

Answer in a clear, structured format. Highlight key legal principles, relevant EU directives, and practical implications.
""")
    
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    rag_chain = (
        RunnableMap({
            "context": retriever | (lambda docs: "\n\n".join([d.page_content for d in docs])),
            "question": RunnablePassthrough()
        })
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain


def get_document_comparison_prompt() -> ChatPromptTemplate:
    """
    Get the prompt template for document comparison with structured JSON output.
    
    Returns:
        A ChatPromptTemplate for comparing documents against regulations.
    """
    return ChatPromptTemplate.from_template("""
You are a legal compliance expert specialized in European regulations (GDPR, AI Act, NIS2, DSA, DMA, etc.).

Your task is to compare an internal policy/procedure document against relevant EU regulations and identify specific discrepancies.

**Internal Document Content:**
{document_content}

**Relevant Regulatory Context:**
{context}

**Instructions:**
1. Analyze the internal document against the regulatory context provided
2. Identify specific discrepancies, gaps, or non-compliance issues
3. For EACH discrepancy, you MUST cite the specific article, section, or recital from the regulation
4. Return your analysis as a JSON object with the following structure:

{{
    "summary": "Brief overview of overall compliance status",
    "discrepancies": [
        {{
            "title": "Title of the discrepancy",
            "issue": "Description of the discrepancy",
            "location_in_document": "Where in the document this appears",
            "regulatory_violation": "Specific regulation/article violated",
            "citation": "Exact article number, e.g., 'GDPR Article 6(1)(a)' or 'AI Act Article 10(2)'",
            "required_action": "What needs to be changed",
            "severity": "High/Medium/Low (optional)"
        }}
    ],
    "compliance_score": 75.0,
    "recommendations": [
        "Actionable step 1",
        "Actionable step 2"
    ]
}}

**Important Requirements:**
- Always cite specific articles when flagging discrepancies (format: "Regulation Name Article X")
- If no discrepancies are found, return an empty discrepancies array
- Compliance score must be a number between 0 and 100
- Return ONLY valid JSON, no additional text or markdown formatting
""")


def get_document_retriever() -> BaseRetriever:
    """
    Get a retriever configured for document comparison (more documents).
    
    Returns:
        BaseRetriever instance configured for document comparison
    """
    return get_retriever(k=DOCUMENT_RETRIEVER_K)

