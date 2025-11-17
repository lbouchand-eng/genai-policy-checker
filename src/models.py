"""
Data models for compliance analysis and discrepancies.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Citation:
    """Represents a regulatory citation."""
    regulation: str  # e.g., "GDPR", "AI Act"
    article: str  # e.g., "6(1)(a)", "10(2)"
    full_citation: str  # e.g., "GDPR Article 6(1)(a)"
    is_validated: bool = False
    source_document: Optional[str] = None
    source_article: Optional[str] = None
    
    def __str__(self) -> str:
        return self.full_citation


@dataclass
class Discrepancy:
    """Represents a compliance discrepancy found in a document."""
    title: str
    issue: str
    location_in_document: str
    regulatory_violation: str
    citation: Citation
    required_action: str
    severity: Optional[str] = None  # e.g., "High", "Medium", "Low"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "issue": self.issue,
            "location_in_document": self.location_in_document,
            "regulatory_violation": self.regulatory_violation,
            "citation": {
                "regulation": self.citation.regulation,
                "article": self.citation.article,
                "full_citation": self.citation.full_citation,
                "is_validated": self.citation.is_validated,
                "source_document": self.citation.source_document,
            },
            "required_action": self.required_action,
            "severity": self.severity,
        }


@dataclass
class ComplianceAnalysis:
    """Structured compliance analysis result."""
    summary: str
    discrepancies: List[Discrepancy] = field(default_factory=list)
    compliance_score: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    analyzed_document: Optional[str] = None
    analysis_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Set analysis date if not provided."""
        if self.analysis_date is None:
            self.analysis_date = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "summary": self.summary,
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "compliance_score": self.compliance_score,
            "recommendations": self.recommendations,
            "analyzed_document": self.analyzed_document,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
        }
    
    @property
    def discrepancy_count(self) -> int:
        """Return the number of discrepancies found."""
        return len(self.discrepancies)
    
    @property
    def has_discrepancies(self) -> bool:
        """Check if any discrepancies were found."""
        return len(self.discrepancies) > 0

