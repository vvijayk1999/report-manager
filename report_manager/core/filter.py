from pydantic import BaseModel
from typing import Optional
from .config import ReportType, ReportCategory


class ReportFilter(BaseModel):
    """Filter parameters for report generation."""

    department_id: Optional[str] = None

    # Report configuration
    report_type: ReportType
    category: ReportCategory
    metrics_type: Optional[str] = None

    # Special flags
    is_instantaneous: bool = False

    class Config:
        use_enum_values = True
