import polars as pl
from typing import Dict, Any, List, Optional, Set, Type, Union
from functools import lru_cache
import importlib
import logging

from .config import ReportConfig, ReportType, ReportCategory
from .filter import ReportFilter
from ..builders.base import BaseReportBuilder
from ..exceptions.report_exceptions import (
    ReportConfigurationError,
    ReportBuilderNotFoundError
)


class ReportManager:
    """
    Central manager for report generation
    with configurable builders and settings.
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialize the report manager with optional configuration."""
        self.config = config or ReportConfig()
        self._builder_registry: Dict[str, Type[BaseReportBuilder]] = {}
        self._register_default_builders()

    def _register_default_builders(self):
        """Register default report builders."""
        default_builders = {
            ReportType.DAYWISE:
                "report_manager.builders.daywise.DaywiseReportBuilder",
            ReportType.WEEKWISE:
                "report_manager.builders.weekwise.WeekwiseReportBuilder",
            ReportType.MONTHWISE:
                "report_manager.builders.monthwise.MonthwiseReportBuilder",
            ReportType.SHIFTWISE:
                "report_manager.builders.shiftwise.ShiftwiseReportBuilder",
            ReportType.INSTANTANEOUS:
            "report_manager.builders.instantaneous.InstantaneousReportBuilder"
        }

        for report_type, builder_path in default_builders.items():
            try:
                self.register_builder(report_type.value, builder_path)
            except ImportError as e:
                logging.warning(
                    f"Could not register default builder "
                    f"for {report_type}: {e}"
                )

    def register_builder(
        self,
        report_type: str,
        builder_class: Union[str, Type[BaseReportBuilder]]
    ):
        """Register a custom report builder."""
        if isinstance(builder_class, str):
            # Dynamic import
            module_path, class_name = builder_class.rsplit('.', 1)
            module = importlib.import_module(module_path)
            builder_class = getattr(module, class_name)

        self._builder_registry[report_type] = builder_class

    @lru_cache(maxsize=32)
    def _validate_department(self, department: str) -> None:
        """Validate department configuration."""
        if department not in self.config.departments:
            raise ReportConfigurationError(
                f"Department '{department}' not configured")

    def _get_builder_class(self, report_type: str) -> Type[BaseReportBuilder]:
        """Get the appropriate builder class for the report type."""
        if report_type not in self._builder_registry:
            raise ReportBuilderNotFoundError(
                f"No builder registered for report type: {report_type}")
        return self._builder_registry[report_type]

    def _prepare_column_configuration(
        self,
        filter_params: ReportFilter,
        grouping_columns: Set[str],
        aggregation_columns: Set[str],
        average_columns: Set[str],
        counting_columns: Set[str],
        simple_counting_columns: Set[str],
        first_value_columns: Set[str]
    ) -> Dict[str, Any]:
        """Prepare column configuration based on department and category."""

        department_config = self.config.departments.get(
            filter_params.department_id)
        if not department_config:
            raise ReportConfigurationError(
                f"Department configuration not found: "
                f"{filter_params.department_id}"
            )

        # Initialize with default grouping columns
        final_grouping_columns = set(self.config.default_grouping_columns)
        final_grouping_columns.update(grouping_columns)

        # Add department-specific product column
        if department_config.product_column:
            final_grouping_columns.add(department_config.product_column)

        # Handle category-specific configurations
        machine_columns = {"asset_id", "machine_name"}

        if filter_params.category in \
                [ReportCategory.COUNTWISE, ReportCategory.HANKWISE]:
            counting_columns.update(machine_columns)
            final_grouping_columns -= machine_columns
        elif filter_params.category == ReportCategory.LOTWISE:
            counting_columns.update(machine_columns)
            if department_config.product_column:
                counting_columns.add(department_config.product_column)
            final_grouping_columns -= counting_columns

        # Add shift columns for shift-based reports
        if filter_params.report_type in \
                [ReportType.SHIFTWISE, ReportType.INSTANTANEOUS]:
            final_grouping_columns.update({"shift_id", "platform_shift_id"})

        return {
            "grouping_columns": final_grouping_columns,
            "aggregation_columns": aggregation_columns,
            "average_columns": average_columns,
            "counting_columns": counting_columns,
            "simple_counting_columns": simple_counting_columns,
            "first_value_columns": first_value_columns
        }

    def _prepare_column_mappings(
        self,
        filter_params: ReportFilter,
        column_mappings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare column mappings with mandatory fields."""
        department_config = self.config.departments.get(
            filter_params.department_id)
        if not department_config:
            return column_mappings

        # Get product column info
        product_column = department_config.product_column
        product_config = self.config.column_definitions.get(product_column)

        # Generate mandatory mappings based on category
        mandatory_mappings = {}

        if filter_params.category == ReportCategory.COUNTWISE:
            if product_config:
                mandatory_mappings.update({
                    product_column: {
                        "name": product_config.name,
                        "unit": product_config.unit,
                        "sort_order": -3
                    },
                })
            mandatory_mappings.update({
                "lot_number": {"name": "Lot name", "sort_order": -2},
                "machine_name": {"name": "No. of M/C", "sort_order": -1}
            })
        elif filter_params.category == ReportCategory.LOTWISE:
            mandatory_mappings.update({
                "lot_number": {"name": "Lot name", "sort_order": -3},
            })
            if product_config:
                mandatory_mappings.update({
                    product_column: {
                        "name": f"No. of {product_config.name}",
                        "unit": product_config.unit,
                        "sort_order": -2
                    },
                })
            mandatory_mappings.update({
                "machine_name": {"name": "No. of M/C", "sort_order": -1}
            })
        elif filter_params.category == ReportCategory.MACHINEWISE:
            mandatory_mappings.update({
                "machine_name": {"name": "M/C Name", "sort_order": -3},
            })
            if product_config:
                mandatory_mappings.update({
                    product_column: {
                        "name": product_config.name,
                        "unit": product_config.unit,
                        "sort_order": -2
                    },
                })
            mandatory_mappings.update({
                "lot_number": {"name": "Lot name", "sort_order": -1}
            })

        column_mappings.update(mandatory_mappings)
        return column_mappings

    def generate_report(self,
                        data_frame: pl.DataFrame,
                        filter_params: Optional[ReportFilter] = None,
                        grouping_columns: Optional[Set[str]] = None,
                        aggregation_columns: Optional[Set[str]] = None,
                        average_columns: Optional[Set[str]] = None,
                        counting_columns: Optional[Set[str]] = None,
                        simple_counting_columns: Optional[Set[str]] = None,
                        first_value_columns: Optional[Set[str]] = None,
                        column_mappings: Optional[Dict[str, Any]] = None,
                        summary_columns: Optional[Set[str]] = None,
                        **kwargs) -> Dict[str, Any]:
        """
        Generate a report based on the provided parameters.

        Args:
            data_frame: Input data for report generation
            filter_params: Report filter parameters
            grouping_columns: Columns to group by
            aggregation_columns: Columns to aggregate
            average_columns: Columns to average
            counting_columns: Complex counting columns
            simple_counting_columns: Simple counting columns
            first_value_columns: Columns to take first value
            column_mappings: Column property mappings
            summary_columns: Columns for summary calculations
            **kwargs: Additional parameters

        Returns:
            Generated report as dictionary
        """

        if not isinstance(data_frame, pl.DataFrame) or data_frame.is_empty():
            raise ValueError("data_frame must be a non-empty Polars DataFrame")

        # Use defaults from config if not provided
        grouping_columns = grouping_columns or set(
            self.config.grouping_columns)
        aggregation_columns = aggregation_columns or set(
            self.config.aggregation_columns)
        average_columns = average_columns or set(
            self.config.average_columns)
        counting_columns = counting_columns or set(
            self.config.counting_columns
        )
        simple_counting_columns = simple_counting_columns or set(
            self.config.simple_counting_columns
        )
        first_value_columns = first_value_columns or set(
            self.config.first_value_columns
        )
        summary_columns = summary_columns or set(
            self.config.summary_columns)
        column_mappings = column_mappings or {
            k: v.dict(include={"name", "sort_order"})
            for k, v in self.config.column_definitions.items()
        }

        # Validate department if filter provided
        if filter_params and filter_params.department_id:
            self._validate_department(filter_params.department_id)

        # Prepare column configuration
        if filter_params:
            column_config = self._prepare_column_configuration(
                filter_params, grouping_columns, aggregation_columns,
                average_columns, counting_columns, simple_counting_columns,
                first_value_columns
            )
            column_mappings = self._prepare_column_mappings(
                filter_params, column_mappings)
        else:
            column_config = {
                "grouping_columns": grouping_columns,
                "aggregation_columns": aggregation_columns,
                "average_columns": average_columns,
                "counting_columns": counting_columns,
                "simple_counting_columns": simple_counting_columns,
                "first_value_columns": first_value_columns
            }

        # Get builder class
        report_type = filter_params.report_type if filter_params else "daywise"
        builder_class = self._get_builder_class(report_type)

        # Create and configure builder
        builder = builder_class()
        builder.set_dataframe(data_frame)
        builder.set_constants_map(self.config.constants)

        # Set formula mappings from config
        formula_mappings = []
        for formula_name, formula_config in self.config.formulas.items():
            formula_mappings.append({
                "column_name": formula_name,
                "formula": formula_config.formula,
                "paramColumnMap": formula_config.parameters,
                "paramConstMap": formula_config.constants or {}
            })
        builder.set_formula_mappings(formula_mappings)

        builder.set_column_mappings(column_mappings)
        builder.set_shift_mapping(self.config.shift_mappings)
        builder.set_group_by_columns(list(column_config["grouping_columns"]))
        builder.set_average_columns(list(column_config["average_columns"]))
        builder.set_first_select_columns(
            list(column_config["first_value_columns"]))
        builder.set_agg_columns(list(column_config["aggregation_columns"]))
        builder.set_counting_columns(list(column_config["counting_columns"]))
        builder.set_simple_counting_columns(
            list(column_config["simple_counting_columns"]))
        builder.set_summary_columns(summary_columns)
        builder.set_roundoff_columns(self.config.precision_defaults)

        # Set any additional parameters from kwargs
        for key, value in kwargs.items():
            setter_method = f"set_{key}"
            if hasattr(builder, setter_method):
                getattr(builder, setter_method)(value)

        return builder.build()

    def get_available_report_types(self) -> List[str]:
        """Get list of available report types."""
        return list(self._builder_registry.keys())

    def get_department_config(
        self,
        department_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific department."""
        dept_config = self.config.departments.get(department_id)
        return dept_config.dict() if dept_config else None
