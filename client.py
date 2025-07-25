import polars as pl
from report_factory import ReportFactory
from data.filter import Filter

data_frame = pl.read_csv("pms_ringframe_shift_2025-07-01.csv")
formula_mappings = []
shift_mapping = {
    "SFM1543487734ac53c35": "Shift 1",
    "SFM1544075171987f271": "Shift 2",
    "SFM154417433e50aa595": "Shift 3"
}
precision_map = {
    "COL12021847878a708eb": 1,
    "COL120218477d88a1b76": 1,
    "COL120218476ac5f14eb": 1,
    "COL1202184766f99af26": 1,
    "COL12021847511b80c66": 1,
    "COL120218474ad1dad65": 1,
    "COL12021847426658bce": 1,
    "COL1202184741cab143c": 1,
    "COL120218473b2fc402a": 1,
    "COL12021847359c7132c": 1,
    "COL1202184729d71888f": 1,
    "COL1202184722f73efa3": 1,
    "COL120218471664670e9": 1,
    "COL1202184715fecb470": 1,
    "COL120218470c522f801": 1,
    "COL1202184370b40ffd0": 1,
    "COL0147203126b2c5135": 1
}
column_map = {
    "COL1202184370b40ffd0": {
        "sortOrder": 0,
        "name": "TPI",
        "unit": None
    },
    "COL120218470c522f801": {
        "sortOrder": 1,
        "name": "TM",
        "unit": None
    },
    "COL120218471664670e9": {
        "sortOrder": 2,
        "name": "Avg. Spindle Speed",
        "unit": "RPM"
    },
    "COL1202184715fecb470": {
        "sortOrder": 3,
        "name": "Avg. Delivery Speed",
        "unit": "M/Min"
    },
    "COL1202184729d71888f": {
        "sortOrder": 4,
        "name": "GPSS",
        "unit": "Gms"
    },
    "COL1202184722f73efa3": {
        "sortOrder": 5,
        "name": "Production Efficiency",
        "unit": "%"
    },
    "COL120218473b2fc402a": {
        "sortOrder": 6,
        "name": "M/c Utilization",
        "unit": "%"
    },
    "COL12021847359c7132c": {
        "sortOrder": 7,
        "name": "Target Production",
        "unit": "Kgs"
    },
    "COL120218474ad1dad65": {
        "sortOrder": 8,
        "name": "Production",
        "unit": "Kgs"
    },
    "COL12021847426658bce": {
        "sortOrder": 9,
        "name": "Total Doffs",
        "unit": "Nos"
    },
    "COL1202184741cab143c": {
        "sortOrder": 10,
        "name": "Avg. Doff Time",
        "unit": "mins"
    },
    "COL12021847511b80c66": {
        "sortOrder": 11,
        "name": "Run Time",
        "unit": "mins"
    },
    "COL1202184766f99af26": {
        "sortOrder": 12,
        "name": "Idle Time",
        "unit": "mins"
    },
    "COL120218476ac5f14eb": {
        "sortOrder": 13,
        "name": "Doff Time",
        "unit": "mins"
    },
    "COL120218477d88a1b76": {
        "sortOrder": 14,
        "name": "Powerfail Time",
        "unit": "mins"
    },
    "COL12021847878a708eb": {
        "sortOrder": 15,
        "name": "UKG",
        "unit": None
    },
    "COL0147203126b2c5135": {
        "sortOrder": 16,
        "name": "Total KWh",
        "unit": "KWh"
    }
}
constants = {
    "CON03052159401f2f800": 0,
    "CON083923861ae562ab5": 1234
}
grouping_columns = [],
average_columns = [
    "COL120218471664670e9",
    "COL12021847511b80c66",
    "COL1202184741cab143c",
    "COL1202184766f99af26",
    "COL120218477d88a1b76",
    "COL1202184729d71888f",
    "COL1202184722f73efa3",
    "COL120218473b2fc402a",
    "COL120218476ac5f14eb",
    "COL1202184715fecb470",
    "COL12021847878a708eb"
]
aggregation_columns = [
    "COL1202184370b40ffd0",
    "COL120218470c522f801",
    "COL120218474ad1dad65",
    "COL12021847359c7132c",
    "COL12021847426658bce",
    "COL0147203126b2c5135"
]
counting_columns = []
simple_counting_columns = []
first_value_columns = []
summary_columns = [
    "COL120218471664670e9",
    "COL12021847511b80c66",
    "COL1202184741cab143c",
    "COL1202184766f99af26",
    "COL120218477d88a1b76",
    "COL120218474ad1dad65",
    "COL1202184729d71888f",
    "COL1202184722f73efa3",
    "COL120218473b2fc402a",
    "COL12021847426658bce",
    "COL12021847359c7132c",
    "COL120218476ac5f14eb",
    "COL1202184715fecb470",
    "COL0147203126b2c5135",
    "COL12021847878a708eb"
]

if __name__ == "__main__":
    report_factory = ReportFactory()
    filter = Filter(
        **{
            "module_id": "pms",
            "department_id": "ringframe",
            "report_type": "shiftwise",
            "start_date": "2025-07-01",
            "end_date": "2025-07-01",
            "metrics_type": "production",
            "category": "machinewise"
        }
    )

    report_builder = report_factory.build(
        filter=filter,
        data_frame=data_frame,
        grouping_columns=grouping_columns,
        aggregation_columns=aggregation_columns,
        average_columns=average_columns,
        simple_counting_columns=simple_counting_columns,
        counting_columns=counting_columns,
        first_value_columns=first_value_columns,
        formula_mappings=formula_mappings,
        shift_mapping=shift_mapping,
        roundoff_columns=precision_map,
        column_mappings=column_map,
        constants=constants,
        summary_columns=summary_columns,
    )

    json_response = report_builder.build()

    print(json_response)
