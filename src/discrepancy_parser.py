"""
Parser for structured discrepancy extraction from LLM responses.

Parses JSON or markdown-formatted compliance analysis into structured data models.
"""
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.models import ComplianceAnalysis, Discrepancy, Citation
from src.exceptions import CitationValidationError


def parse_json_compliance_analysis(
    json_text: str,
    analyzed_document: Optional[str] = None
) -> ComplianceAnalysis:
    """
    Parse JSON-formatted compliance analysis.
    
    Args:
        json_text: JSON string containing compliance analysis
        analyzed_document: Name of the analyzed document
    
    Returns:
        ComplianceAnalysis object
    
    Raises:
        CitationValidationError: If JSON parsing fails
    """
    try:
        # Try to extract JSON from text (in case LLM adds extra text)
        json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        
        data = json.loads(json_text)
        
        # Parse summary
        summary = data.get("summary", "")
        
        # Parse discrepancies
        discrepancies = []
        for disc_data in data.get("discrepancies", []):
            # Extract citation
            citation_text = disc_data.get("citation", "")
            citations = extract_citations_from_text(citation_text)
            citation = citations[0] if citations else Citation(
                regulation="Unknown",
                article="Unknown",
                full_citation=citation_text
            )
            
            discrepancy = Discrepancy(
                title=disc_data.get("title", "Untitled Discrepancy"),
                issue=disc_data.get("issue", ""),
                location_in_document=disc_data.get("location_in_document", ""),
                regulatory_violation=disc_data.get("regulatory_violation", ""),
                citation=citation,
                required_action=disc_data.get("required_action", ""),
                severity=disc_data.get("severity")
            )
            discrepancies.append(discrepancy)
        
        # Parse compliance score
        compliance_score = data.get("compliance_score")
        if isinstance(compliance_score, str):
            # Extract number from string like "75/100"
            score_match = re.search(r'(\d+(?:\.\d+)?)', compliance_score)
            if score_match:
                compliance_score = float(score_match.group(1))
        
        # Parse recommendations
        recommendations = data.get("recommendations", [])
        if isinstance(recommendations, str):
            recommendations = [r.strip() for r in recommendations.split('\n') if r.strip()]
        
        return ComplianceAnalysis(
            summary=summary,
            discrepancies=discrepancies,
            compliance_score=compliance_score,
            recommendations=recommendations,
            analyzed_document=analyzed_document,
            analysis_date=datetime.now()
        )
    
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise CitationValidationError(f"Failed to parse JSON compliance analysis: {str(e)}")


def parse_markdown_compliance_analysis(
    markdown_text: str,
    analyzed_document: Optional[str] = None
) -> ComplianceAnalysis:
    """
    Parse markdown-formatted compliance analysis (fallback method).
    
    Args:
        markdown_text: Markdown text containing compliance analysis
        analyzed_document: Name of the analyzed document
    
    Returns:
        ComplianceAnalysis object
    """
    summary = ""
    discrepancies = []
    compliance_score = None
    recommendations = []
    
    # Extract summary
    summary_match = re.search(r'###\s*Summary\s*\n(.*?)(?=###|\n##|\Z)', markdown_text, re.DOTALL | re.IGNORECASE)
    if summary_match:
        summary = summary_match.group(1).strip()
    
    # Extract discrepancies
    discrepancy_section = re.search(
        r'###\s*Identified\s+Discrepancies\s*\n(.*?)(?=###\s*Compliance\s+Score|###\s*Recommendations|\Z)',
        markdown_text,
        re.DOTALL | re.IGNORECASE
    )
    
    if discrepancy_section:
        disc_text = discrepancy_section.group(1)
        
        # Find individual discrepancies
        disc_pattern = r'####\s*Discrepancy\s+\d+:\s*(.*?)(?=####\s*Discrepancy|\Z)'
        disc_matches = re.finditer(disc_pattern, disc_text, re.DOTALL | re.IGNORECASE)
        
        for match in disc_matches:
            disc_content = match.group(1)
            
            # Extract fields
            title_match = re.search(r'^([^\n]+)', disc_content)
            title = title_match.group(1).strip() if title_match else "Untitled Discrepancy"
            
            issue_match = re.search(r'\*\*Issue:\*\*\s*(.*?)(?=\*\*|$)', disc_content, re.DOTALL)
            issue = issue_match.group(1).strip() if issue_match else ""
            
            location_match = re.search(r'\*\*Location\s+in\s+Document:\*\*\s*(.*?)(?=\*\*|$)', disc_content, re.DOTALL)
            location = location_match.group(1).strip() if location_match else ""
            
            violation_match = re.search(r'\*\*Regulatory\s+Violation:\*\*\s*(.*?)(?=\*\*|$)', disc_content, re.DOTALL)
            violation = violation_match.group(1).strip() if violation_match else ""
            
            citation_match = re.search(r'\*\*Citation:\*\*\s*(.*?)(?=\*\*|$)', disc_content, re.DOTALL)
            citation_text = citation_match.group(1).strip() if citation_match else ""
            
            action_match = re.search(r'\*\*Required\s+Action:\*\*\s*(.*?)(?=\*\*|$)', disc_content, re.DOTALL)
            action = action_match.group(1).strip() if action_match else ""
            
            # Create citation
            citations = extract_citations_from_text(citation_text)
            citation = citations[0] if citations else Citation(
                regulation="Unknown",
                article="Unknown",
                full_citation=citation_text
            )
            
            discrepancy = Discrepancy(
                title=title,
                issue=issue,
                location_in_document=location,
                regulatory_violation=violation,
                citation=citation,
                required_action=action
            )
            discrepancies.append(discrepancy)
    
    # Extract compliance score
    score_match = re.search(r'###\s*Compliance\s+Score\s*\n.*?(\d+(?:\.\d+)?)\s*/?\s*100', markdown_text, re.IGNORECASE)
    if score_match:
        compliance_score = float(score_match.group(1))
    
    # Extract recommendations
    rec_match = re.search(
        r'###\s*Recommendations\s*\n(.*?)(?=\Z)',
        markdown_text,
        re.DOTALL | re.IGNORECASE
    )
    if rec_match:
        rec_text = rec_match.group(1)
        recommendations = [r.strip('- •').strip() for r in rec_text.split('\n') if r.strip() and not r.strip().startswith('#')]
    
    return ComplianceAnalysis(
        summary=summary or "Compliance analysis completed.",
        discrepancies=discrepancies,
        compliance_score=compliance_score,
        recommendations=recommendations,
        analyzed_document=analyzed_document,
        analysis_date=datetime.now()
    )


def extract_citations_from_text(text: str) -> List[Citation]:
    """
    Extract citations from text (helper function).
    
    Args:
        text: Text containing citations
    
    Returns:
        List of Citation objects
    """
    from src.citation_validator import extract_citations
    return extract_citations(text)


def parse_compliance_analysis(
    llm_response: str,
    analyzed_document: Optional[str] = None,
    prefer_json: bool = True
) -> ComplianceAnalysis:
    """
    Parse compliance analysis from LLM response.
    Tries JSON first, falls back to markdown parsing.
    
    Args:
        llm_response: LLM response text
        analyzed_document: Name of the analyzed document
        prefer_json: Whether to prefer JSON parsing
    
    Returns:
        ComplianceAnalysis object
    """
    if prefer_json:
        try:
            return parse_json_compliance_analysis(llm_response, analyzed_document)
        except CitationValidationError:
            # Fall back to markdown parsing
            pass
    
    return parse_markdown_compliance_analysis(llm_response, analyzed_document)

