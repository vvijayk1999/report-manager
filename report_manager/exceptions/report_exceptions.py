class ReportManagerException(Exception):
    """Base exception for report manager."""
    pass


class ReportConfigurationError(ReportManagerException):
    """Raised when there's an error in report configuration."""
    pass


class ReportBuilderNotFoundError(ReportManagerException):
    """Raised when a report builder is not found."""
    pass


class DataValidationError(ReportManagerException):
    """Raised when data validation fails."""
    pass


class FormulaCalculationError(ReportManagerException):
    """Raised when formula calculation fails."""
    pass
