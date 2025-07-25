from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class Filter(BaseModel):
    report_id: Optional[str] = Field(None)
    module_id: Optional[str] = Field(None)
    department_id: Optional[str] = Field(None)
    metrics_type: Optional[str] = Field(None)
    report_type: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    start_date: date = Field(...)
    end_date: date = Field(...)
    platform_shift_ids: Optional[List[str]] = Field(None)
    asset_ids: Optional[List[str]] = Field(None)
    yarn_counts: Optional[List[float]] = Field(None)
    lot_numbers: Optional[List[str]] = Field(None)
    unit_id: Optional[str] = Field(None)
    shed_id: Optional[str] = Field(None)
    is_instantaneous: Optional[bool] = Field(False)
    break_type: Optional[str] = Field(None)
    occurrence_gte: Optional[int] = Field(None)
    duration_gte: Optional[float] = Field(None)
