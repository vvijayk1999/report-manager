"""
Advanced configuration examples for different project types.
"""


def textile_industry_config():
    """Configuration for textile manufacturing reports."""

    return {
        "departments": {
            "ringframe": {
                "product_column": "count_ne",
                "mandatory_columns": ["date", "shift_id", "platform_shift_id", "lot_number", "asset_id"],
                "default_grouping_columns": ["date", "lot_number", "asset_id", "machine_name"]
            },
            "weaving": {
                "product_column": "fabric_type",
                "mandatory_columns": ["date", "shift_id", "loom_id", "beam_id"],
                "default_grouping_columns": ["date", "loom_id", "beam_id"]
            }
        },
        "column_definitions": {
            "count_ne": {"name": "Count", "unit": "Ne", "sort_order": 0},
            "fabric_type": {"name": "Fabric Type", "sort_order": 0},
            "production": {"name": "Production", "unit": "Kg", "sort_order": 1, "precision": 2},
            "efficiency": {"name": "Efficiency", "unit": "%", "sort_order": 2, "precision": 1},
            "spindle_speed": {"name": "Spindle Speed", "unit": "RPM", "sort_order": 3},
            "machine_name": {"name": "Machine", "sort_order": 4}
        },
        "formulas": {
            "production_efficiency": {
                "formula": "actual_production / target_production * 100",
                "parameters": {
                    "actual_production": "production",
                    "target_production": "target_production"
                }
            },
            "utilization": {
                "formula": "run_time / (run_time + idle_time) * 100",
                "parameters": {
                    "run_time": "run_time_minutes",
                    "idle_time": "idle_time_minutes"
                }
            }
        },
        "shift_mappings": {
            "SFM1543487734ac53c35": "Shift 1",
            "SFM1544075171987f271": "Shift 2",
            "SFM154417433e50aa595": "Shift 3"
        },
        "precision_defaults": {
            "production": 2,
            "efficiency": 1,
            "spindle_speed": 0
        }
    }


def automotive_industry_config():
    """Configuration for automotive manufacturing reports."""

    return {
        "departments": {
            "assembly": {
                "product_column": "part_number",
                "mandatory_columns": ["date", "shift_id", "station_id", "batch_id"],
                "default_grouping_columns": ["date", "station_id", "batch_id"]
            },
            "painting": {
                "product_column": "color_code",
                "mandatory_columns": ["date", "shift_id", "booth_id", "job_id"],
                "default_grouping_columns": ["date", "booth_id", "job_id"]
            }
        },
        "column_definitions": {
            "part_number": {"name": "Part Number", "sort_order": 0},
            "color_code": {"name": "Color", "sort_order": 0},
            "units_produced": {"name": "Units Produced", "unit": "units", "sort_order": 1},
            "cycle_time": {"name": "Cycle Time", "unit": "seconds", "sort_order": 2, "precision": 1},
            "defect_rate": {"name": "Defect Rate", "unit": "%", "sort_order": 3, "precision": 2},
            "station_id": {"name": "Station", "sort_order": 4}
        },
        "formulas": {
            "oee": {
                "formula": "availability * performance * quality / 10000",
                "parameters": {
                    "availability": "availability_percent",
                    "performance": "performance_percent",
                    "quality": "quality_percent"
                }
            },
            "throughput": {
                "formula": "units_produced / cycle_time_hours",
                "parameters": {
                    "units_produced": "units_produced",
                    "cycle_time_hours": "total_cycle_time"
                }
            }
        },
        "shift_mappings": {
            "DAY": "Day Shift",
            "NIGHT": "Night Shift",
            "WEEKEND": "Weekend Shift"
        },
        "precision_defaults": {
            "units_produced": 0,
            "cycle_time": 1,
            "defect_rate": 2,
            "oee": 2
        }
    }


def food_processing_config():
    """Configuration for food processing industry reports."""

    return {
        "departments": {
            "packaging": {
                "product_column": "product_sku",
                "mandatory_columns": ["date", "shift_id", "line_id", "batch_id"],
                "default_grouping_columns": ["date", "line_id", "batch_id"]
            },
            "quality_control": {
                "product_column": "test_type",
                "mandatory_columns": ["date", "shift_id", "lab_id", "sample_id"],
                "default_grouping_columns": ["date", "lab_id", "sample_id"]
            }
        },
        "column_definitions": {
            "product_sku": {"name": "Product SKU", "sort_order": 0},
            "test_type": {"name": "Test Type", "sort_order": 0},
            "packages_produced": {"name": "Packages", "unit": "units", "sort_order": 1},
            "weight": {"name": "Weight", "unit": "kg", "sort_order": 2, "precision": 3},
            "temperature": {"name": "Temperature", "unit": "°C", "sort_order": 3, "precision": 1},
            "line_speed": {"name": "Line Speed", "unit": "m/min", "sort_order": 4, "precision": 1}
        },
        "formulas": {
            "yield_percentage": {
                "formula": "output_weight / input_weight * 100",
                "parameters": {
                    "output_weight": "final_weight",
                    "input_weight": "raw_material_weight"
                }
            },
            "line_efficiency": {
                "formula": "actual_speed / rated_speed * 100",
                "parameters": {
                    "actual_speed": "line_speed",
                    "rated_speed": "rated_line_speed"
                }
            }
        },
        "constants": {
            "rated_line_speed": 50.0,
            "target_temperature": 25.0
        },
        "precision_defaults": {
            "weight": 3,
            "temperature": 1,
            "line_speed": 1,
            "yield_percentage": 2
        }
    }


if __name__ == "__main__":
    print("=== Basic Usage Example ===")
    basic_example()

    print("\n=== Configuration File Example ===")
    configuration_file_example()

    print("\n=== Custom Builder Example ===")
    custom_builder_example()
