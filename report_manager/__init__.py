"""
Report Manager Core - A modular, configurable report generation library.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .core.factory import ReportManager
from .core.config import ReportConfig, ConfigLoader, ColumnConfig, FormulaConfig, DepartmentConfig
from .core.filter import ReportFilter, ReportType, ReportCategory
from .exceptions.report_exceptions import (
    ReportManagerException,
    ReportConfigurationError,
    ReportBuilderNotFoundError,
    DataValidationError,
    FormulaCalculationError
)

__all__ = [
    "ReportManager",
    "ReportConfig",
    "ConfigLoader",
    "ColumnConfig",
    "FormulaConfig",
    "DepartmentConfig",
    "ReportFilter",
    "ReportType",
    "ReportCategory",
    "ReportManagerException",
    "ReportConfigurationError",
    "ReportBuilderNotFoundError",
    "DataValidationError",
    "FormulaCalculationError"
]
