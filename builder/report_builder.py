import polars as pl
from typing import Dict, Set, List, Any, Optional
import logging


class ReportBuilder:
    """Base class for building reports from polars DataFrames.

    Provides core functionality for data aggregation, grouping,
    and calculations.
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
            "day",
            "month",
            "year",
            "week_of_month"
        ]
        self.formula_mappings: List[Dict[str, Any]] = []
        self.shift_mapping: Dict[str, str] = {}
        self.roundoff_columns: Dict[str, int] = {}
        self.summary_columns: Set[str] = set()
        self.time_format_mapping: Dict[str, Dict[str, str]] = {}
        self.df: Optional[pl.DataFrame] = None
        self.doff_number_column: Optional[str] = None
        self.department_id: Optional[str] = None

    def set_sorting_columns(self, columns: List[str]) -> 'ReportBuilder':
        """Set sorting columns for the report."""
        self.sorting_columns = columns
        return self

    def set_column_mappings(self, mappings: Dict[str, Any]) -> 'ReportBuilder':
        """Set column mappings for the report."""
        self.column_mappings = mappings
        return self

    def set_dataframe(self, df: pl.DataFrame) -> 'ReportBuilder':
        """Set the input DataFrame for processing."""
        self.df = df
        return self

    def set_shift_mapping(self, sft_mpng: Dict[str, str]) -> 'ReportBuilder':
        self.shift_mapping = sft_mpng
        return self

    def set_formula_mappings(
        self,
        mappings: List[Dict[str, Any]]
    ) -> 'ReportBuilder':
        """Set formula mappings for calculated columns."""
        self.formula_mappings = mappings
        return self

    def set_roundoff_columns(
        self,
        columns: Dict[str, int]
    ) -> 'ReportBuilder':
        """Set columns to be rounded and their decimal places."""
        self.roundoff_columns = columns
        return self

    def set_summary_columns(
        self,
        columns: Set[str]
    ) -> 'ReportBuilder':
        """Set columns to be summarized."""
        self.summary_columns = columns
        return self

    def set_agg_columns(self, columns: List[str]) -> 'ReportBuilder':
        """Set columns to be aggregated."""
        self.agg_columns = columns
        return self

    def set_average_columns(self, columns: List[str]) -> 'ReportBuilder':
        """Set columns to be averaged."""
        self.avg_columns = columns
        return self

    def set_first_select_columns(
        self,
        columns: List[str]
    ) -> 'ReportBuilder':
        """Set columns for first value selection."""
        self.first_select_columns = columns
        return self

    def set_constants_map(
        self,
        constants_map: Dict[str, Any]
    ) -> 'ReportBuilder':
        """Set constants map for formula calculations."""
        self.constants_map = constants_map
        return self

    def set_counting_columns(
        self,
        columns: List[str]
    ) -> 'ReportBuilder':
        """Set columns to be counted."""
        self.counting_columns = columns
        return self

    def set_simple_counting_columns(
        self,
        columns: List[str]
    ) -> 'ReportBuilder':
        """Set columns to be simple counted."""
        self.simple_counting_columns = columns
        return self

    def set_group_by_columns(
        self,
        columns: List[str]
    ) -> 'ReportBuilder':
        """Add additional columns to group by."""
        self.group_by_columns = self.group_by_columns + columns
        return self

    def set_time_format_mapping(
        self,
        time_format_mapping: Dict[str, Dict[str, str]]
    ) -> 'ReportBuilder':
        self.time_format_mapping = time_format_mapping
        return self

    def set_doff_number_column(
        self,
        doff_number_column: str
    ) -> 'ReportBuilder':
        self.doff_number_column = doff_number_column
        return self

    def set_department_id(
        self,
        department_id: str
    ) -> 'ReportBuilder':
        self.department_id = department_id
        return self

    def _add_additional_columns(self) -> None:
        """Add date-based columns to the DataFrame."""
        if "date" not in self.df.columns:
            return

        date_expr = pl.col("date").str.strptime(pl.Date, "%Y-%m-%d")
        self.df = self.df.with_columns([
            date_expr.dt.day().alias("day"),
            date_expr.dt.month().alias("month"),
            date_expr.dt.year().alias("year"),
            ((date_expr.dt.day() - 1) // 7 + 1).alias("week_of_month")
        ])

    def group_data(self, df) -> None:
        """Group and aggregate the DataFrame."""
        aggs = (
            [pl.sum(col) for col in self.agg_columns] +
            [pl.mean(col) for col in self.avg_columns] +
            [pl.n_unique(col) for col in self.counting_columns] +
            [pl.count(col) for col in self.simple_counting_columns] +
            [pl.first(col) for col in self.first_select_columns]
        )
        return df.group_by(self.group_by_columns).agg(aggs)

    def _calculate_summary(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate summary statistics for the given DataFrame."""
        df = df.select(
            [pl.sum(col) for col in self.agg_columns] +
            [pl.mean(col) for col in self.avg_columns] +
            [pl.n_unique(col) for col in self.counting_columns] +
            [pl.count(col) for col in self.simple_counting_columns]
        )
        return df.select(list(self.summary_columns))

    def _add_calculated_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add calculated columns based on formula mappings."""
        def apply_formula(formula: str, kwargs: Dict[str, Any]) -> float:
            try:
                result = eval(formula, {}, kwargs)
                return result
            except ZeroDivisionError:
                return 0
            except Exception as e:
                raise ValueError(
                    f"Error calculating {formula}: {str(e)} | {kwargs}"
                )

        for mapping in self.formula_mappings:
            column_name = mapping["column_name"]
            param_colum_map = mapping["paramColumnMap"]
            param_const_map = mapping.get("paramConstMap", {})

            param_const_val_map = {
                param: self.constants_map[const]
                for param, const in param_const_map.items()
            } if param_const_map else {}

            df = df.with_columns([
                pl.struct(list(param_colum_map.values()))
                .apply(lambda row: apply_formula(
                    mapping["formula"],
                    {k: row[v] for k, v in param_colum_map.items()} |
                    param_const_val_map
                ))
                .alias(column_name)
            ])
        return df

    def roundoff(self, df: pl.DataFrame) -> pl.DataFrame:
        """Round specified columns to their configured decimal places."""
        if not self.roundoff_columns:
            return df

        round_expr = []
        for col in df.columns:
            if (col in self.roundoff_columns and
                    str(df.schema[col]).startswith(('Float32', 'Float64'))):
                round_expr.append(
                    pl.col(col)
                    .round(self.roundoff_columns[col])
                    .alias(col)
                )
            else:
                round_expr.append(pl.col(col))

        return df.select(round_expr)

    def sort_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Filter out columns that do not exist in the DataFrame
        existing_columns = [
            col for col in self.sorting_columns if col in df.columns]
        # Sort by the remaining columns
        return df.sort(existing_columns)

    def prepare_response(self) -> None:
        """Prepare the final response (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement this method")

    def build(self) -> Optional[Any]:
        """Build the final report."""
        if not isinstance(self.df, pl.DataFrame) or self.df.is_empty():
            logging.warning("No valid data loaded or DataFrame is empty.")
            return None

        logging.debug("adding additional columns")
        self._add_additional_columns()
        logging.debug("added additional columns")

        logging.debug("sorting data")
        self.df = self.sort_df(self.df)
        logging.debug("sorted data")

        logging.debug("preparing response")
        return self.prepare_response()
