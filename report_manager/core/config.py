from typing import Dict, Any, List, Optional, Set, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import yaml
import json
from pathlib import Path


class ReportType(str, Enum):
    HOURWISE = "hourwise"
    DAYWISE = "daywise"
    WEEKWISE = "weekwise"
    MONTHWISE = "monthwise"
    SHIFTWISE = "shiftwise"
    INSTANTANEOUS = "instantaneous"
    LOTWISE = "lotwise_consolidated"


class ReportCategory(str, Enum):
    COUNTWISE = "countwise"
    HANKWISE = "hankwise"
    LOTWISE = "lotwise"
    MACHINEWISE = "machinewise"


class ColumnConfig(BaseModel):
    name: str
    unit: Optional[str] = None
    type: str = "string"
    precision: Optional[int] = None
    sort_order: int = 0

    class Config:
        extra = "allow"


class FormulaConfig(BaseModel):
    formula: str
    parameters: Dict[str, str]
    constants: Optional[Dict[str, Any]] = None


class DepartmentConfig(BaseModel):
    product_column: str
    mandatory_columns: List[str] = Field(default_factory=list)
    default_grouping_columns: List[str] = Field(default_factory=list)
    category_mappings: Optional[Dict[str, Dict[str, Any]]] = None


class ReportBuilderConfig(BaseModel):
    builder_class: str
    required_columns: List[str] = Field(default_factory=list)
    optional_columns: List[str] = Field(default_factory=list)
    default_aggregations: Optional[Dict[str, List[str]]] = None


class ReportConfig(BaseModel):
    """Main configuration class for the report manager."""

    # Core settings
    departments: Dict[str, DepartmentConfig] = Field(default_factory=dict)
    report_types: Dict[str, ReportBuilderConfig] = Field(default_factory=dict)
    column_definitions: Dict[str, ColumnConfig] = Field(default_factory=dict)
    formulas: Dict[str, FormulaConfig] = Field(default_factory=dict)

    # Default column groupings
    default_grouping_columns: Set[str] = Field(
        default_factory=lambda: {
            "date", "lot_number", "asset_id", "machine_name"
        }
    )
    mandatory_db_columns: Set[str] = Field(
        default_factory=lambda: {
            "date",
            "shift_id",
            "platform_shift_id",
            "lot_number",
            "asset_id"
        }
    )

    # Global settings
    precision_defaults: Dict[str, int] = Field(default_factory=dict)
    shift_mappings: Dict[str, str] = Field(default_factory=dict)
    constants: Dict[str, Any] = Field(default_factory=dict)

    # Additional fields to handle client configuration style
    grouping_columns: List[str] = Field(default_factory=list)
    aggregation_columns: List[str] = Field(default_factory=list)
    average_columns: List[str] = Field(default_factory=list)
    counting_columns: List[str] = Field(default_factory=list)
    simple_counting_columns: List[str] = Field(default_factory=list)
    first_value_columns: List[str] = Field(default_factory=list)
    summary_columns: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"
        use_enum_values = True

    def __init__(self, **data):
        # Handle the case where multiple dictionaries are merged using **kwargs
        # Extract known top-level lists that might be passed directly
        if 'grouping_columns' in data:
            grouping_columns = data.pop('grouping_columns')
        else:
            grouping_columns = []

        if 'aggregation_columns' in data:
            aggregation_columns = data.pop('aggregation_columns')
        else:
            aggregation_columns = []

        if 'average_columns' in data:
            average_columns = data.pop('average_columns')
        else:
            average_columns = []

        if 'counting_columns' in data:
            counting_columns = data.pop('counting_columns')
        else:
            counting_columns = []

        if 'simple_counting_columns' in data:
            simple_counting_columns = data.pop('simple_counting_columns')
        else:
            simple_counting_columns = []

        if 'first_value_columns' in data:
            first_value_columns = data.pop('first_value_columns')
        else:
            first_value_columns = []

        if 'summary_columns' in data:
            summary_columns = data.pop('summary_columns')
        else:
            summary_columns = []

        super().__init__(
            grouping_columns=grouping_columns,
            aggregation_columns=aggregation_columns,
            average_columns=average_columns,
            counting_columns=counting_columns,
            simple_counting_columns=simple_counting_columns,
            first_value_columns=first_value_columns,
            summary_columns=summary_columns,
            **data
        )

    @validator('departments', pre=True)
    def validate_departments(cls, v):
        if isinstance(v, dict):
            return {
                k: DepartmentConfig(**val)
                if isinstance(val, dict) else val
                for k, val in v.items()
            }
        return v

    @validator('report_types', pre=True)
    def validate_report_types(cls, v):
        if isinstance(v, dict):
            return {
                k: ReportBuilderConfig(**val)
                if isinstance(val, dict) else val
                for k, val in v.items()
            }
        return v

    @validator('column_definitions', pre=True)
    def validate_column_definitions(cls, v):
        if isinstance(v, dict):
            return {k: ColumnConfig(**val) if isinstance(val, dict) else val
                    for k, val in v.items()}
        return v

    @validator('formulas', pre=True)
    def validate_formulas(cls, v):
        if isinstance(v, dict):
            return {k: FormulaConfig(**val) if isinstance(val, dict) else val
                    for k, val in v.items()}
        return v


class ConfigLoader:
    """Utility class for loading configurations from various sources."""

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> ReportConfig:
        """Load configuration from a dictionary."""
        return ReportConfig(**config_dict)

    @staticmethod
    def from_yaml(yaml_path: Union[str, Path]) -> ReportConfig:
        """Load configuration from a YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return ConfigLoader.from_dict(config_dict)

    @staticmethod
    def from_json(json_path: Union[str, Path]) -> ReportConfig:
        """Load configuration from a JSON file."""
        with open(json_path, 'r') as f:
            config_dict = json.load(f)
        return ConfigLoader.from_dict(config_dict)

    @staticmethod
    def merge_configs(
        base_config: ReportConfig,
        override_config: Dict[str, Any]
    ) -> ReportConfig:
        """Merge base configuration with overrides."""
        base_dict = base_config.dict()
        base_dict.update(override_config)
        return ConfigLoader.from_dict(base_dict)
