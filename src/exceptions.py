"""
Custom exception classes for the Policy Compliance Checker.
"""


class PolicyCheckerError(Exception):
    """Base exception for all Policy Checker errors."""
    pass


class DocumentParsingError(PolicyCheckerError):
    """Raised when document parsing fails."""
    pass


class CitationValidationError(PolicyCheckerError):
    """Raised when citation validation fails."""
    pass


class ReportGenerationError(PolicyCheckerError):
    """Raised when report generation fails."""
    pass


class VectorStoreError(PolicyCheckerError):
    """Raised when vector store operations fail."""
    pass

