from typing import Dict, Any, List, Optional, Set, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import yaml
import json
from pathlib import Path
import copy


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


class GroupingType(str, Enum):
    AGGREGATION = "aggregation"
    AVERAGE = "average"
    GROUPING = "grouping"
    COUNTING = "counting"
    SIMPLE_COUNTING = "simple_counting"
    FIRST_VALUE = "first_value"


class ColumnConfig(BaseModel):
    name: str
    unit: Optional[str] = None
    type: str = "string"
    precision: Optional[int] = None
    sort_order: int = 0
    grouping_type: Optional[GroupingType] = None

    class Config:
        extra = "allow"
        use_enum_values = True


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
    # (for backward compatibility)
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

    def get_columns_by_grouping_type(
        self,
        grouping_type: GroupingType
    ) -> List[str]:
        """Get list of columns that have the specified grouping type."""
        return [
            col_name
            for col_name, col_config in self.column_definitions.items()
            if col_config.grouping_type == grouping_type
        ]

    def get_precision_defaults(self) -> Dict[str, int]:
        """Get precision defaults from column definitions
        and legacy precision_defaults."""
        precision_map = {}

        # First, add precision from column definitions
        for col_name, col_config in self.column_definitions.items():
            if col_config.precision is not None:
                precision_map[col_name] = col_config.precision

        # Then, add legacy precision_defaults
        # (they override column-level precision)
        precision_map.update(self.precision_defaults)

        return precision_map

    def get_summary_columns(self) -> Set[str]:
        """Get summary columns from column definitions
        and legacy summary_columns."""
        summary_cols = set(self.summary_columns)

        # Add columns that have aggregation, average, counting,
        # or simple_counting grouping types
        aggregation_types = {
            GroupingType.AGGREGATION,
            GroupingType.AVERAGE,
            GroupingType.COUNTING,
            GroupingType.SIMPLE_COUNTING
        }

        for col_name, col_config in self.column_definitions.items():
            if col_config.grouping_type in aggregation_types:
                summary_cols.add(col_name)

        return summary_cols


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

    @staticmethod
    def _load_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load a single configuration file (YAML or JSON)."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {file_path}")

        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.yml', '.yaml']:
                return yaml.safe_load(f) or {}
            elif file_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(
                    f"Unsupported file format: {file_path.suffix}. "
                    "Only .yaml, .yml, and .json are supported."
                )

    @staticmethod
    def _deep_merge_dicts(
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries,
        with override values taking precedence."""
        result = copy.deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) \
                    and isinstance(value, dict):
                result[key] = ConfigLoader._deep_merge_dicts(
                    result[key], value)
            elif key in result and isinstance(result[key], list) \
                    and isinstance(value, list):
                # For lists, extend the base list
                # with override values (avoiding duplicates)
                result[key] = list(dict.fromkeys(result[key] + value))
            elif key in result and isinstance(result[key], set) \
                    and isinstance(value, (set, list)):
                # For sets, union with override values
                if isinstance(value, list):
                    value = set(value)
                result[key] = result[key].union(value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    @staticmethod
    def from_multiple_files(
        *file_paths: Union[str, Path],
        merge_strategy: str = "deep"
    ) -> ReportConfig:
        """
        Load configuration from multiple files and merge them.

        Args:
            *file_paths: Variable number of file paths to load
            merge_strategy: "deep" for deep merging (default)
            or "shallow" for shallow merging

        Returns:
            ReportConfig: Merged configuration object

        Raises:
            ValueError: If no files are provided or unsupported merge strategy
            FileNotFoundError: If any file doesn't exist
        """
        if not file_paths:
            raise ValueError("At least one file path must be provided")

        if merge_strategy not in ["deep", "shallow"]:
            raise ValueError(
                "merge_strategy must be either 'deep' or 'shallow'")

        # Load the first file as base
        merged_config = ConfigLoader._load_file(file_paths[0])

        # Merge remaining files
        for file_path in file_paths[1:]:
            config_dict = ConfigLoader._load_file(file_path)

            if merge_strategy == "deep":
                merged_config = ConfigLoader._deep_merge_dicts(
                    merged_config, config_dict)
            else:  # shallow merge
                merged_config.update(config_dict)

        return ConfigLoader.from_dict(merged_config)

    @staticmethod
    def from_files_list(
        file_paths: List[Union[str, Path]],
        merge_strategy: str = "deep"
    ) -> ReportConfig:
        """
        Load configuration from a list of files and merge them.

        Args:
            file_paths: List of file paths to load
            merge_strategy: "deep" for deep merging (default)
            or "shallow" for shallow merging

        Returns:
            ReportConfig: Merged configuration object
        """
        return ConfigLoader.from_multiple_files(
            *file_paths, merge_strategy=merge_strategy)

    @staticmethod
    def from_directory(directory_path: Union[str, Path],
                       pattern: str = "*.{yaml,yml,json}",
                       merge_strategy: str = "deep",
                       sort_files: bool = True) -> ReportConfig:
        """
        Load all configuration files from a directory and merge them.

        Args:
            directory_path: Path to directory containing config files
            pattern: Glob pattern for file matching
            (default: "*.{yaml,yml,json}")
            merge_strategy: "deep" for deep merging (default) or
            "shallow" for shallow merging
            sort_files: Whether to sort files before
            merging (ensures consistent order)

        Returns:
            ReportConfig: Merged configuration object

        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If no matching files found
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        # Find all matching files
        config_files = []
        for ext in ['yaml', 'yml', 'json']:
            config_files.extend(directory_path.glob(f"*.{ext}"))

        if not config_files:
            raise ValueError(
                f"No configuration files found in directory: {directory_path}")

        if sort_files:
            config_files.sort()

        return ConfigLoader.from_files_list(
            config_files, merge_strategy=merge_strategy)

    @staticmethod
    def from_mixed_sources(*sources: Union[str, Path, Dict[str, Any]],
                           merge_strategy: str = "deep") -> ReportConfig:
        """
        Load configuration from mixed sources
        (files and dictionaries) and merge them.

        Args:
            *sources: Variable number of sources (file paths or dictionaries)
            merge_strategy: "deep" for deep merging
            (default) or "shallow" for shallow merging

        Returns:
            ReportConfig: Merged configuration object
        """
        if not sources:
            raise ValueError("At least one source must be provided")

        # Process first source
        first_source = sources[0]
        if isinstance(first_source, dict):
            merged_config = copy.deepcopy(first_source)
        else:
            merged_config = ConfigLoader._load_file(first_source)

        # Merge remaining sources
        for source in sources[1:]:
            if isinstance(source, dict):
                config_dict = source
            else:
                config_dict = ConfigLoader._load_file(source)

            if merge_strategy == "deep":
                merged_config = ConfigLoader._deep_merge_dicts(
                    merged_config, config_dict)
            else:  # shallow merge
                merged_config.update(config_dict)

        return ConfigLoader.from_dict(merged_config)
