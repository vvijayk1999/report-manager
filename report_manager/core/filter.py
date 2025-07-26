from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from .config import ReportType, ReportCategory


class ReportFilter(BaseModel):
    """Filter parameters for report generation."""

    # Core identifiers
    report_id: Optional[str] = None
    module_id: Optional[str] = None
    department_id: Optional[str] = None

    # Report configuration
    report_type: ReportType
    category: ReportCategory
    metrics_type: Optional[str] = None

    # Date range
    start_date: date
    end_date: date

    # Optional filters
    platform_shift_ids: Optional[List[str]] = None
    asset_ids: Optional[List[str]] = None
    yarn_counts: Optional[List[float]] = None
    lot_numbers: Optional[List[str]] = None
    unit_id: Optional[str] = None
    shed_id: Optional[str] = None

    # Special flags
    is_instantaneous: bool = False
    break_type: Optional[str] = None
    occurrence_gte: Optional[int] = None
    duration_gte: Optional[float] = None

    class Config:
        use_enum_values = True
