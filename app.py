"""
Main Chainlit application for EU Policy Compliance Checker.

Provides interactive interface for document comparison and question-answering.
"""
import os
import logging
from getpass import getpass
from dotenv import load_dotenv
import chainlit as cl
from langchain_openai import ChatOpenAI

from src.rag import get_rag_chain, get_document_comparison_prompt, get_document_retriever, get_retriever
from src.config import LLM_MODEL, LLM_TEMPERATURE, RETRIEVAL_QUERY_LENGTH, ANALYSIS_DOCUMENT_LENGTH
from src.report_generator import generate_full_compliance_report, generate_document_compliance_report
from src.document_parser import parse_document
from src.discrepancy_parser import parse_compliance_analysis
from src.citation_validator import validate_citations_against_context, get_citation_statistics
from src.exceptions import DocumentParsingError, ReportGenerationError

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") \
    or getpass("Enter your OpenAI API key: ")

# Initialize RAG chain and components
rag_chain = get_rag_chain()
document_comparison_prompt = get_document_comparison_prompt()
document_retriever = get_document_retriever()
llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)


@cl.on_chat_start
async def start():
    """Initialize chat session with welcome message."""
    await cl.Message(
        content=(
            "**Welcome to the EU Policy Compliance Checker**\n\n"
            "**Two ways to use this tool:**\n"
            "1. **Ask a question** about EU regulations (GDPR, AI Act, NIS2, etc.)\n"
            "2. **Upload a document** (PDF, DOCX, TXT) to compare your internal policy/procedure against EU regulations\n\n"
            "I'll analyze it, retrieve relevant laws, flag discrepancies with cited articles, and generate a full compliance report."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Handle incoming messages and file uploads.
    
    Supports two modes:
    1. Document comparison: Upload a document to compare against regulations
    2. Question-answering: Ask questions about EU regulations
    """
    uploaded_files = message.elements if message.elements else []
    
    if uploaded_files:
        # Document comparison mode
        await cl.Message(
            content="**Document detected! Analyzing your policy/procedure against EU regulations...**"
        ).send()
        
        try:
            # Process uploaded file
            uploaded_file = uploaded_files[0]
            file_path = uploaded_file.path
            file_name = uploaded_file.name
            
            # Extract text from document
            await cl.Message(
                content=f"**Extracting text from {file_name}...**"
            ).send()
            
            try:
                document_content = parse_document(file_path)
            except DocumentParsingError as e:
                await cl.Message(
                    content=f"**Error:** {str(e)}"
                ).send()
                return
            
            if not document_content or len(document_content.strip()) < 50:
                await cl.Message(
                    content="**Error:** The document appears to be empty or could not be parsed. Please ensure the file contains readable text."
                ).send()
                return
            
            # Retrieve relevant regulatory context
            await cl.Message(
                content="**Retrieving relevant EU regulations...**"
            ).send()
            
            # Use document content to find relevant regulations
            query_text = document_content[:RETRIEVAL_QUERY_LENGTH]
            relevant_docs = document_retriever.invoke(query_text)
            
            regulatory_context = "\n\n".join([
                f"[Source: {doc.metadata.get('source', 'Unknown')}, Article: {doc.metadata.get('article', 'N/A')}]\n{doc.page_content}"
                for doc in relevant_docs
            ])
            
            # Run document comparison analysis
            await cl.Message(
                content="**Comparing document against regulations and identifying discrepancies...**"
            ).send()
            
            # Format the prompt with actual values
            formatted_prompt = document_comparison_prompt.format(
                context=regulatory_context,
                document_content=document_content[:ANALYSIS_DOCUMENT_LENGTH]
            )
            
            llm_response = llm.invoke(formatted_prompt).content.strip()
            
            # Parse structured compliance analysis
            try:
                compliance_analysis = parse_compliance_analysis(
                    llm_response,
                    analyzed_document=file_name,
                    prefer_json=True
                )
            except Exception as e:
                logger.warning(f"Failed to parse JSON, falling back to markdown: {e}")
                compliance_analysis = parse_compliance_analysis(
                    llm_response,
                    analyzed_document=file_name,
                    prefer_json=False
                )
            
            # Validate citations against retrieved documents
            all_citations = [disc.citation for disc in compliance_analysis.discrepancies]
            validated_citations = validate_citations_against_context(
                all_citations,
                relevant_docs
            )
            
            # Update citations in discrepancies
            for i, citation in enumerate(validated_citations):
                if i < len(compliance_analysis.discrepancies):
                    compliance_analysis.discrepancies[i].citation = citation
            
            # Get citation statistics
            citation_stats = get_citation_statistics(validated_citations)
            logger.info(f"Citation validation: {citation_stats['validated']}/{citation_stats['total_citations']} validated")
            
            # Create short summary
            summary_prompt = f"""
You are an EU compliance expert.
Provide a concise summary (max 6-8 lines) of the compliance analysis below.
Highlight the number of discrepancies found and overall compliance status.

Analysis Summary: {compliance_analysis.summary}
Number of Discrepancies: {compliance_analysis.discrepancy_count}
Compliance Score: {compliance_analysis.compliance_score if compliance_analysis.compliance_score else 'N/A'}

Format your response naturally and clearly in Markdown.
"""
            short_response = llm.invoke(summary_prompt).content.strip()
            
            # Generate detailed PDF report with discrepancies
            try:
                report_path = generate_document_compliance_report(
                    file_name,
                    compliance_analysis
                )
            except ReportGenerationError as e:
                logger.error(f"Failed to generate report: {e}")
                await cl.Message(
                    content=f"**Error:** Failed to generate compliance report: {str(e)}"
                ).send()
                return
            
            # Display summary
            await cl.Message(
                content=short_response + "\n\n**A detailed compliance report with flagged discrepancies and cited articles is available below.**"
            ).send()
            
            # Display PDF report directly in chat
            await cl.Message(
                content="**Your detailed compliance report:**",
                elements=[cl.Pdf(path=report_path, name=os.path.basename(report_path))]
            ).send()
            
        except ValueError as e:
            await cl.Message(content=f"**Error:** {str(e)}").send()
        except Exception as e:
            logger.error(f"Error during document analysis: {e}", exc_info=True)
            await cl.Message(
                content=f"**Error during document analysis:** {str(e)}"
            ).send()
    
    else:
        # Question-answering mode
        question = message.content
        if not question or not question.strip():
            await cl.Message(
                content="**Please provide a question or upload a document to analyze.**"
            ).send()
            return
            
        await cl.Message(
            content="**Analyzing your question... please wait a few seconds.**"
        ).send()

        try:
            # Run RAG pipeline to get answer based on retrieved documents
            rag_answer = rag_chain.invoke(question)
            
            # Get the retrieved documents to show sources
            retriever = get_retriever()
            retrieved_docs = retriever.invoke(question)
            
            # Format answer with source citations
            sources_list = []
            seen_sources = set()
            for doc in retrieved_docs:
                source = doc.metadata.get('source', 'Unknown')
                article = doc.metadata.get('article', '')
                if source not in seen_sources:
                    source_info = f"{source}"
                    if article:
                        source_info += f" (Article {article})"
                    sources_list.append(source_info)
                    seen_sources.add(source)
            
            sources_text = "\n".join([f"- {s}" for s in sources_list[:5]])  # Limit to 5 sources
            
            # Display answer with sources
            response_text = f"{rag_answer}\n\n**Sources:**\n{sources_text}"
            
            await cl.Message(content=response_text).send()

        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            await cl.Message(content=f"**Error during analysis:** {str(e)}").send()
