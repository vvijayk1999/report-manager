from typing import Set, Dict, Any

# Default column sets
DEFAULT_GROUPING_COLUMNS: Set[str] = {
    "date",
    "lot_number",
    "asset_id",
    "machine_name"
}

MANDATORY_DB_COLUMNS: Set[str] = {
    "date",
    "shift_id",
    "platform_shift_id",
    "lot_number",
    "asset_id"
}

# Spinning Industry-specific defaults
SPINNING_DEPARTMENT_PRODUCT_COLUMNS: Dict[str, str] = {
    "ringframe": "count_ne",
    "ringframe_ybs": "count_ne",
    "speedframe": "roving_count",
    "drawframefinisher": "hank_ne",
    "drawframebreaker": "hank_ne",
    "carding": "hank_ne",
    "comber": "hank_ne",
    "lapformer": "target_weight",
}

SPINNING_PRODUCT_COLUMN_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "count_ne": {
        "name": "Count",
        "unit": None
    },
    "roving_count": {
        "name": "Hank",
        "unit": "Ne"
    },
    "hank_ne": {
        "name": "Hank",
        "unit": "Ne"
    },
    "target_weight": {
        "name": "Lap Weight",
        "unit": "Gms/M"
    },
}

# Default report configurations
DEFAULT_REPORT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "textile": {
        "departments": {
            dept: {
                "product_column": col,
                "mandatory_columns": list(MANDATORY_DB_COLUMNS),
                "default_grouping_columns": list(DEFAULT_GROUPING_COLUMNS)
            }
            for dept, col in SPINNING_DEPARTMENT_PRODUCT_COLUMNS.items()
        },
        "column_definitions": {
            col: {
                "name": defn["name"],
                "unit": defn["unit"],
                "sort_order": -1  # Default sort order for product columns
            }
            for col, defn in SPINNING_PRODUCT_COLUMN_DEFINITIONS.items()
        }
    }
}
