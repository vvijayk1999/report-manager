from enum import Enum


class ReportType(Enum):
    HOURWISE = "hourwise"
    DAYWISE = "daywise"
    WEEKWISE = "weekwise"
    MONTHWISE = "monthwise"
    SHIFTWISE = "shiftwise"
    INSTANTANEOUS = "instantaneous"
    LOTWISE = "lotwise_consolidated"


class Department(Enum):
    RINGFRAME = "ringframe"
    RINGFRAME_YBS = "ringframe_ybs"
    SPEEDFRAME = "speedframe"
    DRAWFRAMEFINISHER = "drawframefinisher"
    DRAWFRAMEBREAKER = "drawframebreaker"
    CARDING = "carding"
    COMBER = "comber"
    LAPFORMER = "lapformer"


class ReportCategory(Enum):
    COUNTWISE = "countwise"
    HANKWISE = "hankwise"
    LOTWISE = "lotwise"
    MACHINEWISE = "machinewise"


MANDATORY_DB_COLUMNS = {
    "date",
    "shift_id",
    "platform_shift_id",
    "lot_number",
    "asset_id",
}

DEFAULT_GROUP_COLUMNS = {
    "date",
    "lot_number",
    "asset_id",
    "machine_name"
}

DEPARTMENT_PRODUCT_COLUMN = {
    "ringframe": "count_ne",
    "ringframe_ybs": "count_ne",
    "speedframe": "roving_count",
    "drawframefinisher": "hank_ne",
    "drawframebreaker": "hank_ne",
    "carding": "hank_ne",
    "comber": "hank_ne",
    "lapformer": "target_weight",
}

PRODUCT_COLUMN = {
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