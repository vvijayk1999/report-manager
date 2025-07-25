import polars as pl
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from functools import lru_cache

from data.filter import Filter
from builder.hourwise_rpt_builder import HourwiseRptBuilder
from builder.daywise_rpt_builder import DaywiseRptBuilder
from builder.shiftwise_rpt_builder import ShiftwiseRptBuilder
from builder.weekwise_rpt_builder import WeekwiseRptBuilder
from builder.monthwise_rpt_builder import MonthwiseRptBuilder
from builder.instantaneous_rpt_builder import InstantaneousRptBuilder
from builder.lotwise_consolidated import LotwiseConsolidatedRptBuilder

from util.defaults import (
    DEFAULT_GROUP_COLUMNS,
    DEPARTMENT_PRODUCT_COLUMN,
    PRODUCT_COLUMN,
    ReportType,
    Department,
    ReportCategory
)


@dataclass
class ColumnConfiguration:
    """Data class to hold column configurations for cleaner state management."""
    grouping_columns: Set[str]
    aggregation_columns: Set[str]
    simple_counting_columns: Set[str]
    counting_columns: Set[str]
    first_value_columns: Set[str]
    average_columns: Set[str]

    @classmethod
    def create_empty(cls) -> 'ColumnConfiguration':
        """Create an empty column configuration."""
        return cls(
            grouping_columns=set(),
            aggregation_columns=set(),
            simple_counting_columns=set(),
            counting_columns=set(),
            first_value_columns=set(),
            average_columns=set()
        )


class ReportFactory:
    """
    Factory class for creating different types of reports.

    This class handles the initialization and configuration of various report
    builders based on the requested report type.
    """

    # Class-level builder mapping for better performance
    _BUILDER_MAP = {
        ReportType.HOURWISE: HourwiseRptBuilder,
        ReportType.DAYWISE: DaywiseRptBuilder,
        ReportType.WEEKWISE: WeekwiseRptBuilder,
        ReportType.MONTHWISE: MonthwiseRptBuilder,
        ReportType.SHIFTWISE: ShiftwiseRptBuilder,
        ReportType.INSTANTANEOUS: InstantaneousRptBuilder,
        ReportType.LOTWISE: LotwiseConsolidatedRptBuilder
    }

    # Categories that require shift columns
    _SHIFT_REQUIRING_TYPES = {ReportType.SHIFTWISE, ReportType.INSTANTANEOUS}

    def __init__(self):
        """Initialize the ReportFactory with empty default values."""
        self.report_builder = None
        self.column_config = ColumnConfiguration.create_empty()
        self.data_frame: Optional[pl.DataFrame] = None

    @staticmethod
    @lru_cache(maxsize=32)
    def _validate_department(department: str) -> None:
        """
        Validate department with caching for better performance.

        Args:
            department: Department identifier to validate

        Raises:
            ValueError: If department is invalid
        """
        if department not in [d.value for d in Department]:
            raise ValueError(f"Invalid department: {department}")

    def _init_columns(self, department: str, category: str) -> None:
        """
        Initialize column groupings based on department and category.

        Args:
            department: Department identifier
            category: Report category

        Raises:
            ValueError: If DataFrame is not set or department is invalid
        """
        if self.data_frame is None:
            raise ValueError(
                "DataFrame must be set before initializing columns")

        self._validate_department(department)

        # Initialize with mandatory grouping columns
        self.column_config.grouping_columns = set(DEFAULT_GROUP_COLUMNS)
        self.column_config.grouping_columns.add(
            DEPARTMENT_PRODUCT_COLUMN[department])

        # Configure category-specific columns
        self._configure_category_columns(department, category)

    def _configure_category_columns(self, department: str, category: str) -> None:
        """
        Configure columns based on category type.

        Args:
            department: Department identifier
            category: Report category
        """
        machine_columns = {"asset_id", "machine_name"}

        if category in (ReportCategory.COUNTWISE.value, ReportCategory.HANKWISE.value):
            self.column_config.counting_columns.update(machine_columns)
            self.column_config.grouping_columns -= machine_columns

        elif category == ReportCategory.LOTWISE.value:
            counting_columns = machine_columns.copy()
            counting_columns.add(DEPARTMENT_PRODUCT_COLUMN[department])
            self.column_config.counting_columns.update(counting_columns)
            self.column_config.grouping_columns -= counting_columns

        # MACHINEWISE category requires no special handling

    def _get_mandatory_column_mappings(self, department: str, category: str) -> Dict[str, Any]:
        """
        Generate mandatory column mappings based on department and category.

        Args:
            department: Department identifier
            category: Report category

        Returns:
            Dictionary of mandatory column mappings
        """
        column_id = DEPARTMENT_PRODUCT_COLUMN[department]
        column_name = PRODUCT_COLUMN[column_id]

        # Define base mappings for each category
        mapping_configs = {
            "countwise": [
                (column_id, column_name["name"], column_name["unit"], -3),
                ("lot_number", "Lot name", None, -2),
                ("machine_name", "No. of M/C", None, -1)
            ],
            "lotwise": [
                ("lot_number", "Lot name", None, -3),
                (column_id,
                 f"No. of {column_name['name']}", column_name["unit"], -2),
                ("machine_name", "No. of M/C", None, -1)
            ],
            "machinewise": [
                ("machine_name", "M/C Name", None, -3),
                (column_id, column_name["name"], column_name["unit"], -2),
                ("lot_number", "Lot name", None, -1)
            ]
        }

        mappings = {}
        if category in mapping_configs:
            for col_id, name, unit, sort_order in mapping_configs[category]:
                mapping = {"name": name, "sortOrder": sort_order}
                if unit:
                    mapping["unit"] = unit
                mappings[col_id] = mapping

        return mappings

    def _inject_mandatory_column_mappings(
        self,
        column_mappings: Dict[str, Any],
        department: str,
        category: str
    ) -> Dict[str, Any]:
        """
        Add mandatory column mappings to existing mappings.

        Args:
            column_mappings: Existing column property mappings
            department: Department identifier
            category: Report category

        Returns:
            Updated column mappings including mandatory fields
        """
        mandatory_mappings = self._get_mandatory_column_mappings(
            department, category)
        column_mappings.update(mandatory_mappings)
        return column_mappings

    def _get_report_builder(self, report_type: str):
        """
        Create appropriate report builder based on report type.

        Args:
            report_type: Type of report to generate

        Returns:
            Initialized report builder instance

        Raises:
            ValueError: If report type is invalid
        """
        try:
            report_enum = ReportType(report_type.lower())
        except ValueError:
            raise ValueError(f"Invalid report type: {report_type}")

        # Get builder class from mapping
        builder_class = self._BUILDER_MAP.get(report_enum)
        if not builder_class:
            raise ValueError(
                f"No builder found for report type: {report_type}")

        builder = builder_class()

        # Add shift columns if required
        if report_enum in self._SHIFT_REQUIRING_TYPES:
            self.column_config.grouping_columns.update(
                {"shift_id", "platform_shift_id"})

        return builder

    def _configure_report_builder(
        self,
        builder,
        data_frame: pl.DataFrame,
        formula_mappings: List[Dict[str, Any]],
        shift_mapping: Dict[str, str],
        roundoff_columns: Dict[str, int],
        column_mappings: Dict[str, Any],
        constants: Dict[str, Any],
        summary_columns: Set[str]
    ):
        """Configure the report builder with all necessary parameters."""
        builder.set_dataframe(data_frame)
        builder.set_constants_map(constants)
        builder.set_formula_mappings(formula_mappings)
        builder.set_column_mappings(column_mappings)
        builder.set_shift_mapping(shift_mapping)
        builder.set_group_by_columns(list(self.column_config.grouping_columns))
        builder.set_average_columns(list(self.column_config.average_columns))
        builder.set_first_select_columns(
            list(self.column_config.first_value_columns))
        builder.set_agg_columns(list(self.column_config.aggregation_columns))
        builder.set_counting_columns(list(self.column_config.counting_columns))
        builder.set_simple_counting_columns(
            list(self.column_config.simple_counting_columns))
        builder.set_summary_columns(summary_columns)
        builder.set_roundoff_columns(roundoff_columns)

    def build(
        self,
        filter: Filter,
        data_frame: pl.DataFrame,
        grouping_columns: Set[str],
        aggregation_columns: Set[str],
        average_columns: Set[str],
        simple_counting_columns: Set[str],
        counting_columns: Set[str],
        first_value_columns: Set[str],
        formula_mappings: List[Dict[str, Any]],
        shift_mapping: Dict[str, str],
        roundoff_columns: Dict[str, int],
        column_mappings: Dict[str, Any],
        constants: Dict[str, Any],
        summary_columns: Set[str]
    ):
        """
        Build and configure a report builder based on input parameters.

        Args:
            filter: Filter parameters for the report
            data_frame: Input data for report generation
            grouping_columns: Columns to group by
            aggregation_columns: Columns to aggregate
            average_columns: Columns to average
            simple_counting_columns: Simple counting columns
            counting_columns: Complex counting columns  
            first_value_columns: Columns to take first value
            formula_mappings: List of formula configurations
            shift_mapping: Shift identifier mappings
            time_format_mapping: Time format configurations
            roundoff_columns: Precision settings for numeric columns
            column_mappings: Column property mappings
            constants: Global constants used in report generation
            doff_number_column: Doff number column identifier
            summary_columns: Columns for summary calculations

        Returns:
            Configured report builder instance

        Raises:
            ValueError: If required parameters are invalid
        """
        if not isinstance(data_frame, pl.DataFrame):
            raise ValueError("data_frame must be a Polars DataFrame")

        # Store configurations
        self.data_frame = data_frame
        self.column_config.grouping_columns = grouping_columns
        self.column_config.average_columns = average_columns
        self.column_config.aggregation_columns = aggregation_columns
        self.column_config.counting_columns = counting_columns
        self.column_config.simple_counting_columns = simple_counting_columns
        self.column_config.first_value_columns = first_value_columns

        # Update column mappings with mandatory fields
        column_mappings = self._inject_mandatory_column_mappings(
            column_mappings=column_mappings,
            category=filter.category,
            department=filter.department_id
        )

        # Initialize column groupings
        self._init_columns(
            department=filter.department_id,
            category=filter.category
        )

        # Create and configure report builder
        self.report_builder = self._get_report_builder(filter.report_type)

        self._configure_report_builder(
            self.report_builder,
            data_frame,
            formula_mappings,
            shift_mapping,
            roundoff_columns,
            column_mappings,
            constants,
            summary_columns
        )

        return self.report_builder
