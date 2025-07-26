from typing import Dict, Any
import polars as pl

from ..builders.base import BaseReportBuilder


class HourwiseReportBuilder(BaseReportBuilder):
    def set_end_time_column(self, end_time_column: str):
        self.end_time_column = end_time_column
        return self

    def prepare_response(self) -> Dict[str, Any]:
        # Process overall summary in one chain
        overall_summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.format_time)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )

        records = (
            self.group_data(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.format_time)
            .pipe(self.roundoff)
            .pipe(self.sort_df)
        )

        records = records.with_columns(
            pl.col(self.end_time_column).str.extract(
                r"(\d{2}:\d{2})$", group_index=1).alias(self.end_time_column)
        )

        records = records.to_dicts()

        filtered_records = [
            {
                **{
                    key: record[key]
                    for key in record
                    if key in self.column_mappings
                },
                'asset_id': record.get('asset_id', None)
            }
            for record in records
        ]

        sections = [
            {
                "subsections": [{"records": filtered_records}]
            }
        ]

        return {
            "report_type": "hourwise",
            "sections": sections,
            "summary_label": "overall summary",
            "summary": overall_summary,
            "column_header_mapping": self.column_mappings,
        }
