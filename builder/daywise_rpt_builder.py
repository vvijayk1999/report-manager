from typing import Dict, Any
from datetime import datetime

from builder.report_builder import ReportBuilder


class DaywiseRptBuilder(ReportBuilder):
    def prepare_response(self) -> Dict[str, Any]:
        # Process overall summary in one chain
        overall_summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )

        sections = []
        # Process each day's data
        for (year, month, day), day_group in self.df.group_by(
                ["year", "month", "day"]):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"

            # Process day summary and records in chains
            day_summary = (
                self._calculate_summary(day_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.roundoff)
                .to_dicts()[0]
            )

            records = (
                self.group_data(day_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.roundoff)
                .pipe(self.sort_df)
                .to_dicts()
            )

            # Add sequential doff_number
            if self.doff_number_column:
                for i, record in enumerate(records, 1):
                    record[self.doff_number_column] = i

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

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %b %Y")

            sections.append(
                {
                    "title": formatted_date,
                    "subsections": [{"records": filtered_records}],
                    "summary_label": f"{formatted_date} summary",
                    "summary": day_summary,
                    "date": date_str
                }
            )

        return {
            "report_type": "daywise",
            "sections": sorted(sections, key=lambda x: x["date"]),
            "summary_label": "overall summary",
            "summary": overall_summary,
            "column_header_mapping": self.column_mappings,
        }
