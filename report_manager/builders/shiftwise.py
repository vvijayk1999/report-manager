from typing import Dict, Any
from datetime import datetime

from ..builders.base import BaseReportBuilder


class ShiftwiseReportBuilder(BaseReportBuilder):
    def prepare_response(self) -> Dict[str, Any]:
        # Calculate overall summary once
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

            # Calculate day summary
            day_summary = (
                self._calculate_summary(day_group)
                .pipe(self._add_calculated_columns)
                .pipe(self.roundoff)
                .to_dicts()[0]
            )

            subsections = []
            # Process each subgroup within the day
            for (shift_id, p_shift_id), group_df in day_group.group_by(
                    ["shift_id", "platform_shift_id"]):
                # Process group records
                records = (
                    self.group_data(group_df)
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

                # Process group summary
                group_summary = (
                    self._calculate_summary(group_df)
                    .pipe(self._add_calculated_columns)
                    .pipe(self.roundoff)
                    .to_dicts()[0]
                )

                # Format group title
                group_title = self.shift_mapping.get(p_shift_id, p_shift_id)
                group_title = f"{group_title}"

                subsections.append(
                    {
                        "title": group_title,
                        "records": filtered_records,
                        "summary_label": f"{group_title} summary",
                        "summary": group_summary,
                        "shift_id": shift_id
                    }
                )
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %b %Y")

            subsections = sorted(subsections, key=lambda x: x["shift_id"])
            sections.append(
                {
                    "title": formatted_date,
                    "subsections": subsections,
                    "summary_label": f"{formatted_date} summary",
                    "summary": day_summary,
                    "date": date_str
                }
            )

        return {
            "report_type": "monthwise",
            "sections": sorted(sections, key=lambda x: x["date"]),
            "summary_label": "overall summary",
            "summary": overall_summary,
            "column_header_mapping": self.column_mappings,
        }
