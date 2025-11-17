"""
PDF report generation module for compliance analysis reports.

Generates structured PDF reports from compliance analysis data.
"""
import logging
from datetime import datetime
from typing import Optional, List
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import markdown
import re

from langchain_openai import ChatOpenAI
from src.models import ComplianceAnalysis, Discrepancy
from src.exceptions import ReportGenerationError
from src.config import OUTPUT_DIR

logger = logging.getLogger(__name__)


def generate_full_compliance_report(question: str, rag_answer: str) -> str:
    """
    Generate a full compliance report for question-answering mode.
    
    Args:
        question: User's question
        rag_answer: Answer from RAG pipeline
    
    Returns:
        Path to generated PDF file
    
    Raises:
        ReportGenerationError: If report generation fails
    """
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

        prompt = f"""
You are a legal compliance expert specialized in EU law, GDPR, and AI regulation.

Based on the following analysis, decide first if the user is **describing a project, company, or internal policy**.
If yes, include a compliance score (e.g. "Compliance Score: 75/100") and give concrete recommendations.
If the user is only asking an informational or general question, **do not include any compliance score**.

Structure your report as follows:
- **Executive Summary**
- *(Optional)* **Compliance Score** (only if relevant)
- **Detailed Analysis**
- **Specific, Actionable Next Steps**

Use clear Markdown formatting:
- Use '## ' for section titles
- Use bold (**...**) for key terms
- Add blank lines between sections and bullet points
- Keep the report concise (max 2 pages)

Analysis:
\"\"\"{rag_answer}\"\"\"

Question: "{question}"
"""

        response = llm.invoke(prompt)
        markdown_text = response.content.strip()

        # Remove duplicate compliance scores
        markdown_text = re.sub(
            r"(Compliance Score\s*[:\-]?\s*\d{1,3}\s*/\s*100)[\s\S]*?(Compliance Score\s*[:\-]?\s*\d{1,3}\s*/\s*100)?",
            r"\1",
            markdown_text,
            flags=re.IGNORECASE,
        )

        # Convert Markdown to HTML
        html_text = markdown.markdown(markdown_text)

        # Create PDF
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"compliance_report_{timestamp}.pdf"
        filepath = OUTPUT_DIR / filename

        styles = getSampleStyleSheet()
        normal = ParagraphStyle(
            "Normal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        )
        title = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=12,
            textColor="#1a1a1a",
        )
        section = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor="#000000",
        )

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            leftMargin=60,
            rightMargin=60,
            topMargin=60,
            bottomMargin=50,
        )

        story = []

        # Header
        story.append(Paragraph("<b>Compliance Analysis Report</b>", title))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y, %H:%M')}", normal))
        story.append(Paragraph(f"<b>Question:</b> {question}", normal))
        story.append(Spacer(1, 12))

        # Add content converted from Markdown to HTML
        for section_html in re.split(r"<h2.*?>(.*?)</h2>", html_text):
            if not section_html.strip():
                continue
            # Check if this is a section title
            if re.match(r'^[A-Z].*', section_html.strip()) and len(section_html.strip()) < 100:
                story.append(Paragraph(f"<b>{section_html.strip()}</b>", section))
            else:
                # Clean up lists and add line breaks
                clean_html = (
                    section_html
                    .replace("</li>", "<br/><br/>")
                    .replace("<ul>", "")
                    .replace("</ul>", "")
                    .replace("<p>", "")
                    .replace("</p>", "<br/><br/>")
                )
                story.append(Paragraph(clean_html, normal))
                story.append(Spacer(1, 6))

        # Footer
        story.append(Spacer(1, 12))
        story.append(Paragraph("<i>Generated automatically by the Policy Checker.</i>", normal))

        doc.build(story)
        logger.info(f"Compliance report saved as {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise ReportGenerationError(f"Error generating report: {str(e)}")


def generate_document_compliance_report(
    document_name: str,
    compliance_analysis: ComplianceAnalysis
) -> str:
    """
    Generate a detailed compliance report for document comparison.
    
    Args:
        document_name: Name of the analyzed document
        compliance_analysis: Structured compliance analysis data
    
    Returns:
        Path to generated PDF file
    
    Raises:
        ReportGenerationError: If report generation fails
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_doc_name = re.sub(r'[^\w\s-]', '', document_name)[:50]
        filename = f"compliance_report_{timestamp}_{safe_doc_name}.pdf"
        filepath = OUTPUT_DIR / filename

        styles = getSampleStyleSheet()
        normal = ParagraphStyle(
            "Normal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        )
        title = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=12,
            textColor="#1a1a1a",
        )
        section = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor="#000000",
        )
        discrepancy_title = ParagraphStyle(
            "DiscrepancyTitle",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
            textColor="#cc0000",
        )

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            leftMargin=60,
            rightMargin=60,
            topMargin=60,
            bottomMargin=50,
        )

        story = []

        # Header
        story.append(Paragraph("<b>Document Compliance Analysis Report</b>", title))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y, %H:%M')}", normal))
        story.append(Paragraph(f"<b>Document Analyzed:</b> {document_name}", normal))
        story.append(Spacer(1, 12))

        # Summary
        story.append(Paragraph("<b>Summary</b>", section))
        story.append(Paragraph(compliance_analysis.summary, normal))
        story.append(Spacer(1, 12))

        # Compliance Score
        if compliance_analysis.compliance_score is not None:
            story.append(Paragraph("<b>Compliance Score</b>", section))
            score_text = f"{compliance_analysis.compliance_score:.1f}/100"
            story.append(Paragraph(score_text, normal))
            story.append(Spacer(1, 12))

        # Discrepancies
        if compliance_analysis.has_discrepancies:
            story.append(Paragraph("<b>Identified Discrepancies</b>", section))
            story.append(Spacer(1, 6))
            
            for i, discrepancy in enumerate(compliance_analysis.discrepancies, 1):
                # Discrepancy title
                disc_title = f"Discrepancy {i}: {discrepancy.title}"
                story.append(Paragraph(f"<b>{disc_title}</b>", discrepancy_title))
                
                # Issue
                story.append(Paragraph(f"<b>Issue:</b> {discrepancy.issue}", normal))
                
                # Location
                story.append(Paragraph(f"<b>Location in Document:</b> {discrepancy.location_in_document}", normal))
                
                # Regulatory violation
                story.append(Paragraph(f"<b>Regulatory Violation:</b> {discrepancy.regulatory_violation}", normal))
                
                # Required action
                story.append(Paragraph(f"<b>Required Action:</b> {discrepancy.required_action}", normal))
                
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("<b>Identified Discrepancies</b>", section))
            story.append(Paragraph("No discrepancies found. The document appears compliant with the analyzed regulations.", normal))
            story.append(Spacer(1, 12))

        # Recommendations
        if compliance_analysis.recommendations:
            story.append(Paragraph("<b>Recommendations</b>", section))
            for rec in compliance_analysis.recommendations:
                story.append(Paragraph(f"• {rec}", normal))
            story.append(Spacer(1, 12))

        # Footer
        story.append(Spacer(1, 12))
        story.append(Paragraph("<i>Generated automatically by the Policy Checker.</i>", normal))

        doc.build(story)
        logger.info(f"Document compliance report saved as {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Failed to generate document compliance report: {e}")
        raise ReportGenerationError(f"Error generating report: {str(e)}")


