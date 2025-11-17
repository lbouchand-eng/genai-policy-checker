"""
Citation extraction and validation module.

Validates that citations mentioned in LLM responses actually exist
in the retrieved regulatory documents.
"""
import re
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document

from src.models import Citation
from src.exceptions import CitationValidationError


def extract_citations(text: str) -> List[Citation]:
    """
    Extract citations from text using regex patterns.
    
    Supports multiple formats:
    - "GDPR Article 6(1)(a)"
    - "AI Act Article 10(2)"
    - "Article 6 GDPR"
    - "Art. 6 GDPR"
    
    Args:
        text: Text containing citations (e.g., "GDPR Article 6(1)(a)")
    
    Returns:
        List of Citation objects extracted from the text
    """
    citations = []
    
    # Pattern 1: "Regulation Article X" or "Regulation Art. X"
    pattern1 = r'((?:GDPR|AI\s+Act|NIS2|NIS\s+2|DSA|DMA|CNIL|Digital\s+Services\s+Act|Digital\s+Markets\s+Act|General\s+Data\s+Protection\s+Regulation)[\s,]+(?:Article|art\.?|Art\.?)[\s]+([\d\(\)a-z,\s]+))'
    
    # Pattern 2: "Article X Regulation" (reversed order)
    pattern2 = r'((?:Article|art\.?|Art\.?)[\s]+([\d\(\)a-z,\s]+)[\s,]+(?:GDPR|AI\s+Act|NIS2|NIS\s+2|DSA|DMA|CNIL|Digital\s+Services\s+Act|Digital\s+Markets\s+Act|General\s+Data\s+Protection\s+Regulation))'
    
    # Pattern 3: Just "Article X" with regulation context nearby (within 50 chars)
    pattern3 = r'(?:GDPR|AI\s+Act|NIS2|NIS\s+2|DSA|DMA|CNIL|Digital\s+Services\s+Act|Digital\s+Markets\s+Act|General\s+Data\s+Protection\s+Regulation)[\s\S]{0,50}?(?:Article|art\.?|Art\.?)[\s]+([\d\(\)a-z,\s]+)'
    
    all_matches = []
    
    # Try pattern 1
    for match in re.finditer(pattern1, text, re.IGNORECASE):
        full_citation = match.group(1).strip()
        article = match.group(2).strip()
        
        # Extract regulation name
        regulation_match = re.match(r'^([A-Za-z\s]+?)\s+(?:Article|art\.?|Art\.?)', full_citation, re.IGNORECASE)
        if regulation_match:
            regulation = regulation_match.group(1).strip()
            all_matches.append((regulation, article, full_citation))
    
    # Try pattern 2
    for match in re.finditer(pattern2, text, re.IGNORECASE):
        article = match.group(2).strip()
        regulation_part = match.group(3).strip()
        full_citation = match.group(1).strip()
        
        # Normalize regulation name
        regulation = normalize_regulation_name(regulation_part)
        all_matches.append((regulation, article, full_citation))
    
    # Try pattern 3 (less reliable, but catches more cases)
    for match in re.finditer(pattern3, text, re.IGNORECASE):
        article = match.group(1).strip()
        # Find regulation name before the match
        start_pos = max(0, match.start() - 100)
        context = text[start_pos:match.start()]
        regulation_match = re.search(r'(GDPR|AI\s+Act|NIS2|NIS\s+2|DSA|DMA|CNIL|Digital\s+Services\s+Act|Digital\s+Markets\s+Act|General\s+Data\s+Protection\s+Regulation)', context, re.IGNORECASE)
        if regulation_match:
            regulation = normalize_regulation_name(regulation_match.group(1))
            full_citation = f"{regulation} Article {article}"
            all_matches.append((regulation, article, full_citation))
    
    # Convert to Citation objects
    for regulation, article, full_citation in all_matches:
        # Normalize regulation name
        regulation = normalize_regulation_name(regulation)
        
        # Clean article number (remove extra spaces)
        article = re.sub(r'\s+', '', article)
        
        citation = Citation(
            regulation=regulation,
            article=article,
            full_citation=full_citation
        )
        citations.append(citation)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_citations = []
    for citation in citations:
        # Use a normalized key for deduplication
        key = (citation.regulation.upper(), citation.article)
        if key not in seen:
            seen.add(key)
            unique_citations.append(citation)
    
    return unique_citations


def normalize_regulation_name(name: str) -> str:
    """
    Normalize regulation names to standard forms.
    
    Args:
        name: Raw regulation name from text
    
    Returns:
        Normalized regulation name
    """
    name_upper = name.upper().strip()
    
    # Map variations to standard names
    normalization_map = {
        'GDPR': 'GDPR',
        'GENERAL DATA PROTECTION REGULATION': 'GDPR',
        'AI ACT': 'AI Act',
        'ARTIFICIAL INTELLIGENCE ACT': 'AI Act',
        'NIS2': 'NIS2',
        'NIS 2': 'NIS2',
        'DSA': 'DSA',
        'DIGITAL SERVICES ACT': 'DSA',
        'DMA': 'DMA',
        'DIGITAL MARKETS ACT': 'DMA',
        'CNIL': 'CNIL',
    }
    
    # Check for exact matches first
    for key, value in normalization_map.items():
        if key in name_upper:
            return value
    
    # Return original if no match (normalize case)
    return name.strip()


def validate_citation_against_document(
    citation: Citation,
    document: Document
) -> bool:
    """
    Validate that a citation exists in a retrieved document.
    
    Uses multiple strategies:
    1. Check metadata (source and article number)
    2. Search for citation text in document content
    3. Search for article number patterns in content
    4. Flexible matching for regulation names and article numbers
    
    Args:
        citation: Citation to validate
        document: Retrieved document to check against
    
    Returns:
        True if citation is found in document, False otherwise
    """
    doc_source = document.metadata.get('source', '').upper()
    doc_article = document.metadata.get('article')
    content = document.page_content
    
    # Normalize regulation names for comparison
    regulation_aliases = {
        'GDPR': ['GDPR', 'GENERAL DATA PROTECTION REGULATION', 'GDPR_', 'GDPR-', 'REGULATION (EU) 2016/679'],
        'AI ACT': ['AI ACT', 'ARTIFICIAL INTELLIGENCE ACT', 'AI_ACT', 'AI-ACT', 'REGULATION (EU) 2024/1689'],
        'NIS2': ['NIS2', 'NIS 2', 'NIS_2', 'DIRECTIVE (EU) 2022/2555'],
        'DSA': ['DSA', 'DIGITAL SERVICES ACT', 'DIGITAL_SERVICES_ACT', 'REGULATION (EU) 2022/2065'],
        'DMA': ['DMA', 'DIGITAL MARKETS ACT', 'DIGITAL_MARKETS_ACT', 'REGULATION (EU) 2022/1925'],
        'CNIL': ['CNIL'],
    }
    
    # Normalize citation regulation name
    citation_reg_normalized = normalize_regulation_name(citation.regulation).upper()
    matches_regulation = False
    matched_regulation = None
    
    # Check if regulation matches in metadata
    for reg, aliases in regulation_aliases.items():
        if any(alias in citation_reg_normalized for alias in aliases):
            # Check if document source matches regulation
            if any(alias in doc_source for alias in aliases):
                matches_regulation = True
                matched_regulation = reg
                break
    
    # If regulation doesn't match in metadata, try to find it in content
    if not matches_regulation:
        content_upper = content.upper()
        for reg, aliases in regulation_aliases.items():
            if any(alias in citation_reg_normalized for alias in aliases):
                # Check if regulation name appears in content
                for alias in aliases:
                    if alias in content_upper:
                        matches_regulation = True
                        matched_regulation = reg
                        break
                if matches_regulation:
                    break
    
    # Also check if document source filename contains regulation name
    if not matches_regulation:
        # Extract filename from source (remove path and extension)
        import os
        source_filename = os.path.basename(doc_source).upper()
        for reg, aliases in regulation_aliases.items():
            if any(alias in citation_reg_normalized for alias in aliases):
                for alias in aliases:
                    if alias in source_filename:
                        matches_regulation = True
                        matched_regulation = reg
                        break
                if matches_regulation:
                    break
    
    if not matches_regulation:
        return False
    
    # Extract base article number from citation (e.g., "6(1)(a)" -> "6")
    article_base_match = re.match(r'^(\d+)', citation.article)
    article_base = article_base_match.group(1) if article_base_match else None
    
    if not article_base:
        return False
    
    # Strategy 1: Check metadata article number (exact or base match)
    if doc_article:
        doc_article_str = str(doc_article).strip()
        doc_article_clean = re.sub(r'[^\d]', '', doc_article_str)
        citation_article_clean = re.sub(r'[^\d]', '', citation.article)
        
        # Check if base numbers match
        if article_base == doc_article_clean or article_base in doc_article_clean:
            citation.is_validated = True
            citation.source_document = document.metadata.get('source')
            citation.source_article = doc_article_str
            return True
        
        # Also check if citation article is contained in doc article (for sub-articles)
        if citation_article_clean and citation_article_clean in doc_article_clean:
            citation.is_validated = True
            citation.source_document = document.metadata.get('source')
            citation.source_article = doc_article_str
            return True
    
    # Strategy 2: Search for citation text in content (case-insensitive)
    content_lower = content.lower()
    citation_text_lower = citation.full_citation.lower()
    
    # Try full citation match
    if citation_text_lower in content_lower:
        citation.is_validated = True
        citation.source_document = document.metadata.get('source')
        citation.source_article = citation.article
        return True
    
    # Strategy 3: Search for "Article X" pattern in content with regulation context
    # Look for patterns like "Article 6", "Article 6(1)", "Article 6(1)(a)"
    article_patterns = [
        rf'\barticle\s+{re.escape(citation.article.lower())}\b',
        rf'\barticle\s+{re.escape(citation.article)}\b',
        rf'\bart\.\s+{re.escape(citation.article.lower())}\b',
        rf'\bart\.\s+{re.escape(citation.article)}\b',
    ]
    
    # Also try with base article number
    if article_base:
        article_patterns.extend([
            rf'\barticle\s+{re.escape(article_base)}\b',
            rf'\barticle\s+{re.escape(article_base)}\s*\(',
            rf'\bart\.\s+{re.escape(article_base)}\b',
            rf'\bart\.\s+{re.escape(article_base)}\s*\(',
        ])
    
    for pattern in article_patterns:
        matches = re.finditer(pattern, content_lower)
        for match in matches:
            # Verify regulation context is nearby (within 300 chars)
            pattern_pos = match.start()
            context_start = max(0, pattern_pos - 300)
            context_end = min(len(content_lower), pattern_pos + len(match.group()) + 300)
            context = content_lower[context_start:context_end]
            
            # Check if regulation name appears in context
            for alias in regulation_aliases.get(matched_regulation, []):
                if alias.lower() in context:
                    citation.is_validated = True
                    citation.source_document = document.metadata.get('source')
                    citation.source_article = citation.article
                    return True
    
    # Strategy 4: Search for article number with flexible context
    # Look for "Article X" anywhere in content, then check if regulation is in document
    article_context_pattern = rf'\barticle\s+{re.escape(article_base)}\b'
    if re.search(article_context_pattern, content_lower):
        # If we found the article number and regulation matches, validate
        citation.is_validated = True
        citation.source_document = document.metadata.get('source')
        citation.source_article = article_base
        return True
    
    return False


def validate_citations_against_context(
    citations: List[Citation],
    retrieved_documents: List[Document]
) -> List[Citation]:
    """
    Validate all citations against retrieved regulatory documents.
    
    Args:
        citations: List of citations to validate
        retrieved_documents: Documents retrieved from vector store
    
    Returns:
        List of citations with validation status updated
    """
    import logging
    logger = logging.getLogger(__name__)
    
    validated_citations = []
    
    logger.info(f"Validating {len(citations)} citations against {len(retrieved_documents)} documents")
    
    # Log all citations being validated
    for i, citation in enumerate(citations):
        logger.info(f"Citation {i+1}: {citation.full_citation} (Regulation: {citation.regulation}, Article: {citation.article})")
    
    # Log document sources for debugging
    doc_sources = {}
    for doc in retrieved_documents:
        source = doc.metadata.get('source', 'Unknown')
        article = doc.metadata.get('article', 'N/A')
        if source not in doc_sources:
            doc_sources[source] = []
        doc_sources[source].append(article)
    
    logger.info(f"Retrieved documents from sources: {list(doc_sources.keys())}")
    for source, articles in doc_sources.items():
        logger.info(f"  - {source}: articles {articles[:10]}...")  # Show first 10 articles
    
    for citation in citations:
        is_valid = False
        validation_attempts = []
        
        for doc_idx, doc in enumerate(retrieved_documents):
            doc_source = doc.metadata.get('source', 'Unknown')
            doc_article = doc.metadata.get('article', 'N/A')
            
            if validate_citation_against_document(citation, doc):
                is_valid = True
                logger.info(f"✓ Validated {citation.full_citation} in document {doc_idx+1}: {doc_source} (Article {doc_article})")
                break
            else:
                validation_attempts.append(f"Doc {doc_idx+1}: {doc_source} (Art {doc_article})")
        
        if not is_valid:
            logger.warning(f"✗ Could not validate {citation.full_citation}")
            logger.debug(f"  Attempted against: {', '.join(validation_attempts[:5])}")  # Show first 5 attempts
        
        validated_citations.append(citation)
    
    validated_count = sum(1 for c in validated_citations if c.is_validated)
    logger.info(f"Validation result: {validated_count}/{len(citations)} citations validated")
    
    return validated_citations


def get_citation_statistics(citations: List[Citation]) -> Dict[str, Any]:
    """
    Get statistics about citation validation.
    
    Args:
        citations: List of citations
    
    Returns:
        Dictionary with validation statistics
    """
    total = len(citations)
    validated = sum(1 for c in citations if c.is_validated)
    unvalidated = total - validated
    
    return {
        "total_citations": total,
        "validated": validated,
        "unvalidated": unvalidated,
        "validation_rate": validated / total if total > 0 else 0.0
    }

