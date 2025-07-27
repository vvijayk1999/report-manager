from typing import Dict, Any
from datetime import datetime

from ..builders.base import BaseReportBuilder


class MonthwiseReportBuilder(BaseReportBuilder):
    def prepare_response(self) -> Dict[str, Any]:
        # Process overall summary in one chain
        overall_summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )

        sections = []
        # Process each month's data
        for (year, month), month_group in self.df.group_by(["year", "month"]):
            month_yr_str = f"{year:04d}-{month:02d}"

            # Process month summary and records in chains
            month_summary = (
                self._calculate_summary(month_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.roundoff)
                .to_dicts()[0]
            )
            # remove unwanted columns from group by columns
            for column in ["day", "month", "year", "date", "week_of_month"]:
                try:
                    self.group_by_columns.remove(column)
                except ValueError:
                    pass

            records = (
                self.group_data(month_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.roundoff)
                .pipe(self.sort_df)
                .to_dicts()
            )

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

            date_obj = datetime(year, month, 1)
            month_yr_str = date_obj.strftime("%B %Y")

            sections.append(
                {
                    "title": month_yr_str,
                    "subsections": [{"records": filtered_records}],
                    "summary_label": f"{month_yr_str} summary",
                    "summary": month_summary,
                    "year_month": f"{year:04d}-{month:02d}",
                }
            )

        return {
            "report_type": "monthwise",
            "sections": sorted(sections, key=lambda x: x["year_month"]),
            "summary_label": "overall summary",
            "summary": overall_summary,
            "column_header_mapping": self.column_mappings,
        }
