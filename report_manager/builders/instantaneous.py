from typing import Dict, Any

from ..builders.base import BaseReportBuilder


class InstantaneousReportBuilder(BaseReportBuilder):
    def prepare_response(self) -> Dict[str, Any]:
        # Calculate overall summary once
        overall_summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )

        # Process each shift's data
        for shift_id, group_df in self.df.group_by(
                "platform_shift_id"):
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

        return {
            "report_type": "instantaneous",
            "sections": {
                "subsections": {
                    "records": filtered_records
                }
            },
            "summary_label": "overall summary",
            "summary": overall_summary,
            "column_header_mapping": self.column_mappings,
        }
