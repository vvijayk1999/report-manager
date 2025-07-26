import polars as pl
from typing import Dict, Set, List, Any, Optional
import logging
from abc import ABC, abstractmethod

from ..exceptions.report_exceptions import DataValidationError, FormulaCalculationError


class BaseReportBuilder(ABC):
    """
    Abstract base class for all report builders.

    Provides core functionality for data aggregation, grouping, and calculations.
    Designed to be extended by specific report implementations.
    """

    def __init__(self) -> None:
        """Initialize the report builder with default values."""
        self.column_mappings: Optional[Dict[str, Any]] = None
        self.sorting_columns: List[str] = []
        self.agg_columns: List[str] = []
        self.avg_columns: List[str] = []
        self.counting_columns: List[str] = []
        self.simple_counting_columns: List[str] = []
        self.first_select_columns: List[str] = []
        self.constants_map: Dict[str, Any] = {}
        self.group_by_columns: List[str] = [
            "day", "month", "year", "week_of_month"]
        self.formula_mappings: List[Dict[str, Any]] = []
        self.shift_mapping: Dict[str, str] = {}
        self.roundoff_columns: Dict[str, int] = {}
        self.summary_columns: Set[str] = set()
        self.time_format_mapping: Dict[str, Dict[str, str]] = {}
        self.df: Optional[pl.DataFrame] = None
        self.doff_number_column: Optional[str] = None
        self.department_id: Optional[str] = None

    # Configuration setters with method chaining
    def set_sorting_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Set sorting columns for the report."""
        self.sorting_columns = columns
        return self

    def set_column_mappings(self, mappings: Dict[str, Any]) -> 'BaseReportBuilder':
        """Set column mappings for the report."""
        self.column_mappings = mappings
        return self

    def set_dataframe(self, df: pl.DataFrame) -> 'BaseReportBuilder':
        """Set the input DataFrame for processing."""
        if not isinstance(df, pl.DataFrame):
            raise DataValidationError("Input must be a Polars DataFrame")
        if df.is_empty():
            raise DataValidationError("DataFrame cannot be empty")
        self.df = df
        return self

    def set_shift_mapping(self, sft_mpng: Dict[str, str]) -> 'BaseReportBuilder':
        """Set shift mapping for the report."""
        self.shift_mapping = sft_mpng
        return self

    def set_formula_mappings(self, mappings: List[Dict[str, Any]]) -> 'BaseReportBuilder':
        """Set formula mappings for calculated columns."""
        self.formula_mappings = mappings
        return self

    def set_roundoff_columns(self, columns: Dict[str, int]) -> 'BaseReportBuilder':
        """Set columns to be rounded and their decimal places."""
        self.roundoff_columns = columns
        return self

    def set_summary_columns(self, columns: Set[str]) -> 'BaseReportBuilder':
        """Set columns to be summarized."""
        self.summary_columns = columns
        return self

    def set_agg_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Set columns to be aggregated."""
        self.agg_columns = columns
        return self

    def set_average_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Set columns to be averaged."""
        self.avg_columns = columns
        return self

    def set_first_select_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Set columns for first value selection."""
        self.first_select_columns = columns
        return self

    def set_constants_map(self, constants_map: Dict[str, Any]) -> 'BaseReportBuilder':
        """Set constants map for formula calculations."""
        self.constants_map = constants_map
        return self

    def set_counting_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Set columns to be counted."""
        self.counting_columns = columns
        return self

    def set_simple_counting_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Set columns to be simple counted."""
        self.simple_counting_columns = columns
        return self

    def set_group_by_columns(self, columns: List[str]) -> 'BaseReportBuilder':
        """Add additional columns to group by."""
        self.group_by_columns = self.group_by_columns + columns
        return self

    def set_time_format_mapping(self, time_format_mapping: Dict[str, Dict[str, str]]) -> 'BaseReportBuilder':
        """Set time format mapping."""
        self.time_format_mapping = time_format_mapping
        return self

    def set_doff_number_column(self, doff_number_column: str) -> 'BaseReportBuilder':
        """Set doff number column."""
        self.doff_number_column = doff_number_column
        return self

    def set_department_id(self, department_id: str) -> 'BaseReportBuilder':
        """Set department ID."""
        self.department_id = department_id
        return self

    # Core data processing methods
    def _add_additional_columns(self) -> None:
        """Add date-based columns to the DataFrame."""
        if "date" not in self.df.columns:
            return

        try:
            date_expr = pl.col("date").str.strptime(pl.Date, "%Y-%m-%d")
            self.df = self.df.with_columns([
                date_expr.dt.day().alias("day"),
                date_expr.dt.month().alias("month"),
                date_expr.dt.year().alias("year"),
                ((date_expr.dt.day() - 1) // 7 + 1).alias("week_of_month")
            ])
        except Exception as e:
            raise DataValidationError(
                f"Error processing date column: {str(e)}")

    def group_data(self, df: pl.DataFrame) -> pl.DataFrame:
        """Group and aggregate the DataFrame."""
        try:
            aggs = (
                [pl.sum(col).alias(col) for col in self.agg_columns if col in df.columns] +
                [pl.mean(col).alias(col) for col in self.avg_columns if col in df.columns] +
                [pl.n_unique(col).alias(col) for col in self.counting_columns if col in df.columns] +
                [pl.count(col).alias(col) for col in self.simple_counting_columns if col in df.columns] +
                [pl.first(col).alias(col)
                 for col in self.first_select_columns if col in df.columns]
            )

            # Filter group by columns to only include existing columns
            existing_group_columns = [
                col for col in self.group_by_columns if col in df.columns]

            if not existing_group_columns:
                raise DataValidationError(
                    "No valid grouping columns found in DataFrame")

            return df.group_by(existing_group_columns).agg(aggs)
        except Exception as e:
            raise DataValidationError(f"Error grouping data: {str(e)}")

    def _calculate_summary(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate summary statistics for the given DataFrame."""
        try:
            summary_expressions = []

            # Add aggregation expressions for existing columns
            for col in self.agg_columns:
                if col in df.columns:
                    summary_expressions.append(pl.sum(col).alias(col))

            for col in self.avg_columns:
                if col in df.columns:
                    summary_expressions.append(pl.mean(col).alias(col))

            for col in self.counting_columns:
                if col in df.columns:
                    summary_expressions.append(pl.n_unique(col).alias(col))

            for col in self.simple_counting_columns:
                if col in df.columns:
                    summary_expressions.append(pl.count(col).alias(col))

            if not summary_expressions:
                raise DataValidationError("No valid summary columns found")

            result_df = df.select(summary_expressions)

            # Filter to only include summary columns that exist
            existing_summary_cols = [
                col for col in self.summary_columns if col in result_df.columns]
            if existing_summary_cols:
                return result_df.select(existing_summary_cols)

            return result_df
        except Exception as e:
            raise DataValidationError(f"Error calculating summary: {str(e)}")

    def _add_calculated_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add calculated columns based on formula mappings."""
        def safe_eval_formula(formula: str, kwargs: Dict[str, Any]) -> float:
            """Safely evaluate formula with error handling."""
            try:
                # Create a safe evaluation environment
                safe_globals = {
                    "__builtins__": {},
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "round": round,
                    "pow": pow,
                }
                result = eval(formula, safe_globals, kwargs)
                return float(result) if result is not None else 0.0
            except ZeroDivisionError:
                return 0.0
            except (TypeError, ValueError):
                return 0.0
            except Exception as e:
                raise FormulaCalculationError(
                    f"Error calculating formula '{formula}': {str(e)}")

        try:
            for mapping in self.formula_mappings:
                column_name = mapping["column_name"]
                param_column_map = mapping["paramColumnMap"]
                param_const_map = mapping.get("paramConstMap", {})

                # Map constants
                param_const_val_map = {}
                for param, const in param_const_map.items():
                    if const in self.constants_map:
                        param_const_val_map[param] = self.constants_map[const]

                # Check if all required columns exist
                missing_columns = [
                    col for col in param_column_map.values() if col not in df.columns]
                if missing_columns:
                    logging.warning(
                        f"Skipping formula for {column_name}: missing columns {missing_columns}")
                    continue

                df = df.with_columns([
                    pl.struct(list(param_column_map.values()))
                    .map_elements(lambda row: safe_eval_formula(
                        mapping["formula"],
                        {k: row[v] for k, v in param_column_map.items()
                         } | param_const_val_map
                    ), return_dtype=pl.Float64)
                    .alias(column_name)
                ])
        except Exception as e:
            raise FormulaCalculationError(
                f"Error adding calculated columns: {str(e)}")

        return df

    def roundoff(self, df: pl.DataFrame) -> pl.DataFrame:
        """Round specified columns to their configured decimal places."""
        if not self.roundoff_columns:
            return df

        try:
            round_expr = []
            for col in df.columns:
                if (col in self.roundoff_columns and
                    col in df.columns and
                        str(df.schema[col]).startswith(('Float32', 'Float64'))):
                    round_expr.append(
                        pl.col(col).round(
                            self.roundoff_columns[col]).alias(col)
                    )
                else:
                    round_expr.append(pl.col(col))

            return df.select(round_expr)
        except Exception as e:
            raise DataValidationError(f"Error rounding columns: {str(e)}")

    def sort_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """Sort DataFrame by configured sorting columns."""
        try:
            # Filter out columns that do not exist in the DataFrame
            existing_columns = [
                col for col in self.sorting_columns if col in df.columns]

            if existing_columns:
                return df.sort(existing_columns)

            # If no sorting columns specified or exist, return as-is
            return df
        except Exception as e:
            logging.warning(f"Error sorting DataFrame: {str(e)}")
            return df

    def format_time(self, df: pl.DataFrame) -> pl.DataFrame:
        """Format time columns based on time format mapping."""
        if not self.time_format_mapping:
            return df

        try:
            for column, format_config in self.time_format_mapping.items():
                if column in df.columns:
                    input_format = format_config.get(
                        "input_format", "%H:%M:%S")
                    output_format = format_config.get("output_format", "%H:%M")

                    df = df.with_columns([
                        pl.col(column)
                        .str.strptime(pl.Time, input_format)
                        .dt.strftime(output_format)
                        .alias(column)
                    ])
        except Exception as e:
            logging.warning(f"Error formatting time columns: {str(e)}")

        return df

    @abstractmethod
    def prepare_response(self) -> Dict[str, Any]:
        """Prepare the final response (to be implemented by subclasses)."""
        raise NotImplementedError(
            "Subclasses must implement prepare_response method")

    def validate_required_columns(self, required_columns: List[str]) -> None:
        """Validate that required columns exist in the DataFrame."""
        if not self.df:
            raise DataValidationError("DataFrame not set")

        missing_columns = [
            col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise DataValidationError(
                f"Required columns missing: {missing_columns}")

    def build(self) -> Optional[Dict[str, Any]]:
        """Build the final report."""
        if not isinstance(self.df, pl.DataFrame) or self.df.is_empty():
            logging.warning("No valid data loaded or DataFrame is empty.")
            return None

        try:
            logging.debug("Adding additional columns")
            self._add_additional_columns()

            logging.debug("Sorting data")
            self.df = self.sort_df(self.df)

            logging.debug("Preparing response")
            return self.prepare_response()

        except Exception as e:
            logging.error(f"Error building report: {str(e)}")
            raise
