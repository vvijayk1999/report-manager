from typing import Dict, Any, Optional
from builder.report_builder import ReportBuilder


class LotwiseConsolidatedRptBuilder(ReportBuilder):

    def prepare_response(self) -> Dict[str, Any]:
        """Prepare the consolidated report grouped by lot number"""
        transformed_df = (
            self.df.pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
        )
        numeric_cols = [
            col
            for col in transformed_df.columns
            if transformed_df[col].is_numeric() and col in self.column_mappings
        ]

        # Process each lot group
        groups = []
        lot_groups = transformed_df.group_by("lot_number")

        for lot_number, group_df in lot_groups:
            # Prepare data records
            records = group_df.select(self.column_mappings.keys()).to_dicts()
            summary = []

            if numeric_cols:
                summary_rows = {
                    "Maximum": {
                        col: group_df[col].max() for col in numeric_cols
                    },
                    "Minimum": {
                        col: group_df[col].min() for col in numeric_cols
                    },
                    "Average": {
                        col: group_df[col].mean() for col in numeric_cols
                    },
                }

                summary = [
                    {
                        **self._create_summary_row(values),
                        "summary_label": label
                    }
                    for label, values in summary_rows.items()
                ]

            groups.append(
                {
                    "lot_number": lot_number,
                    "records": records,
                    "summary": summary,
                }
            )

        return {
            "report_type": "lotwise_consolidated",
            "sections": groups,
            "column_header_mapping": self.column_mappings,
        }

    def _create_summary_row(
        self,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a summary row dictionary"""
        row = {}
        for col, val in values.items():
            row[col] = (
                self._format_value(val, col_name=col)
                if val is not None
                else None
            )
        return row

    def _format_value(self, value: Any, col_name: Optional[str] = None) -> Any:
        """Apply consistent formatting to summary values"""
        if isinstance(value, float):
            return float(round(value, 1))
        return value
