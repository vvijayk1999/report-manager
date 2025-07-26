from typing import Dict, Any
import calendar
from datetime import datetime, timedelta

from ..builders.base import BaseReportBuilder


class WeekwiseReportBuilder(BaseReportBuilder):
    def week_to_day_range(self, year: int, month: int, week_no: int) -> str:
        """Convert week number to date range string."""
        # Get month details
        _, num_days_in_month = calendar.monthrange(year, month)
        first_day_date = datetime(year, month, 1)

        # Calculate week dates
        start_of_week = first_day_date + timedelta(days=(week_no - 1) * 7)
        if start_of_week.month != month:
            return "Invalid week number for the given month"

        # Calculate end date with month boundary check
        end_of_week = min(
            start_of_week +
            timedelta(days=6), datetime(year, month, num_days_in_month)
        )
        result = f"Week {week_no} - ({start_of_week.strftime('%d %b')} - " \
                 f"{end_of_week.strftime('%d %b %Y')})"
        return result

    def prepare_response(self) -> Dict[str, Any]:
        # Process overall summary in one chain
        overall_summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.format_time)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )

        sections = []
        # Process each week's data
        for (year, month, week), week_group in self.df.group_by(
            ["year", "month", "week_of_month"]
        ):
            # Get week range string
            week_str = self.week_to_day_range(year, month, week)

            # Process week summary and records in chains
            week_summary = (
                self._calculate_summary(week_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.format_time)
                .pipe(self.roundoff)
                .to_dicts()[0]
            )

            # remove unwanted columns from group by columns
            for column in ["day", "month", "year", "date"]:
                try:
                    self.group_by_columns.remove(column)
                except ValueError:
                    pass

            records = (
                self.group_data(week_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.format_time)
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

            sections.append(
                {
                    "title": week_str,
                    "subsections": [{"records": filtered_records}],
                    "summary_label": f"{week_str} summary",
                    "year": year,
                    "month": month,
                    "week_of_month": week,
                    "summary": week_summary,
                }
            )

        # Sort sections by year, month, and week
        sections.sort(key=lambda x: (
            x["year"], x["month"], x["week_of_month"]))

        return {
            "report_type": "weekwise",
            "sections": sections,
            "summary_label": "overall summary",
            "summary": overall_summary,
            "column_header_mapping": self.column_mappings,
        }
