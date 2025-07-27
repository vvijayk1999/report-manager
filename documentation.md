# Report Manager Core Documentation

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Configuration System](#configuration-system)
- [Report Builders](#report-builders)
- [Usage Examples](#usage-examples)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Report Manager Core is a modular, configurable report generation library specifically designed for Industrial IoT (IIoT) applications. It provides a flexible framework for generating time-based reports with complex aggregations, calculations, and customizable formatting.

### Key Features

- **Modular Architecture**: Extensible builder pattern with pluggable report types
- **Multiple Report Types**: Daywise, weekwise, monthwise, shiftwise, and instantaneous reports
- **Flexible Configuration**: YAML/JSON-based configuration with inheritance and merging
- **Formula Engine**: Built-in support for calculated columns with formula expressions
- **Data Validation**: Comprehensive input validation and error handling
- **Industry-Specific**: Optimized for textile/spinning industry with department-specific configurations
- **High Performance**: Built on Polars for fast data processing

### Supported Report Types

| Report Type | Description | Use Case |
|-------------|-------------|----------|
| `daywise` | Daily aggregated reports | Daily production summaries |
| `weekwise` | Weekly aggregated reports | Weekly performance analysis |
| `monthwise` | Monthly aggregated reports | Monthly production reports |
| `shiftwise` | Shift-based reports grouped by day | Shift performance tracking |
| `instantaneous` | Real-time/current data reports | Live monitoring dashboards |

### Supported Categories

| Category | Description | Data Grouping |
|----------|-------------|---------------|
| `countwise` | Product count-based reports | By product count and lot |
| `hankwise` | Hank/weight-based reports | By hank measurements |
| `lotwise` | Lot-consolidated reports | By production lots |
| `machinewise` | Machine-specific reports | By individual machines |

## Architecture

The library follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│              Client Code                │
├─────────────────────────────────────────┤
│            ReportManager                │  ← Main entry point
├─────────────────────────────────────────┤
│     Configuration & Filter System      │  ← ReportConfig, ReportFilter
├─────────────────────────────────────────┤
│          Report Builders               │  ← Specific report implementations
├─────────────────────────────────────────┤
│            Base Builder                │  ← Common functionality
├─────────────────────────────────────────┤
│          Data Processing               │  ← Polars DataFrame operations
└─────────────────────────────────────────┘
```

### Core Design Patterns

1. **Factory Pattern**: `ReportManager` creates appropriate builders
2. **Builder Pattern**: Fluent configuration of report parameters
3. **Strategy Pattern**: Pluggable report generation strategies
4. **Template Method**: Base builder defines processing flow

## Installation

### Requirements

- Python 3.8+
- Polars >= 0.20.10
- Pydantic >= 1.10.13
- PyYAML >= 6.0
- typing-extensions >= 4.0.0

### Installation Methods

#### From Source
```bash
git clone <repository-url>
cd report-manager-core
pip install -e .
```

#### Development Installation
```bash
pip install -e ".[dev,docs]"
```

## Quick Start

### Basic Usage

```python
import polars as pl
from report_manager import ReportManager, ReportFilter, ReportType, ReportCategory

# Create sample data
data = pl.DataFrame({
    "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
    "shift_id": [1, 2, 1],
    "platform_shift_id": ["A", "B", "A"],
    "lot_number": ["LOT001", "LOT002", "LOT001"],
    "asset_id": ["M001", "M002", "M001"],
    "machine_name": ["Machine1", "Machine2", "Machine1"],
    "production_qty": [100, 150, 120],
    "count_ne": ["20/1", "30/1", "20/1"]
})

# Initialize report manager
manager = ReportManager()

# Create filter parameters
filter_params = ReportFilter(
    department_id="ringframe",
    report_type=ReportType.DAYWISE,
    category=ReportCategory.COUNTWISE
)

# Generate report
report = manager.generate_report(
    data_frame=data,
    filter_params=filter_params,
    aggregation_columns={"production_qty"},
    column_mappings={
        "production_qty": {"name": "Production Quantity", "unit": "Kg"}
    }
)

print(report)
```

### Configuration-Based Usage

```python
from report_manager import ReportManager, ConfigLoader

# Load configuration from file
config = ConfigLoader.from_yaml("config.yaml")
manager = ReportManager(config)

# Generate report with configuration
report = manager.generate_report(data_frame=data, filter_params=filter_params)
```

## Core Components

### 1. ReportManager

The main orchestrator that coordinates report generation.

```python
from report_manager import ReportManager, ReportConfig

# Initialize with default config
manager = ReportManager()

# Initialize with custom config
config = ReportConfig(
    departments={
        "production": {
            "product_column": "count_ne",
            "mandatory_columns": ["date", "lot_number"]
        }
    }
)
manager = ReportManager(config)
```

**Key Methods:**
- `generate_report()`: Main method for report generation
- `register_builder()`: Register custom report builders
- `get_available_report_types()`: List available report types
- `get_department_config()`: Get department-specific configuration

### 2. ReportFilter

Defines the parameters for report generation.

```python
from report_manager import ReportFilter, ReportType, ReportCategory

filter_params = ReportFilter(
    department_id="ringframe",
    report_type=ReportType.DAYWISE,
    category=ReportCategory.COUNTWISE,
    metrics_type="production",
    is_instantaneous=False
)
```

### 3. ReportConfig

Central configuration management with support for complex configurations.

```python
from report_manager import ReportConfig, ColumnConfig, FormulaConfig

config = ReportConfig(
    column_definitions={
        "efficiency": ColumnConfig(
            name="Efficiency",
            unit="%",
            type="float",
            precision=2,
            grouping_type="average"
        )
    },
    formulas={
        "efficiency": FormulaConfig(
            formula="(actual_production / target_production) * 100",
            parameters={
                "actual_production": "production_qty",
                "target_production": "target_qty"
            }
        )
    }
)
```

## Configuration System

### Configuration Structure

The configuration system supports multiple levels of customization:

#### Basic Configuration Example

```yaml
# config.yaml
departments:
  ringframe:
    product_column: "count_ne"
    mandatory_columns:
      - "date"
      - "lot_number"
      - "asset_id"
    default_grouping_columns:
      - "lot_number"
      - "machine_name"

column_definitions:
  production_qty:
    name: "Production Quantity"
    unit: "Kg"
    type: "float"
    precision: 2
    grouping_type: "aggregation"
    sort_order: 1
  
  efficiency:
    name: "Efficiency"
    unit: "%"
    type: "float"
    precision: 1
    grouping_type: "average"
    sort_order: 2

formulas:
  efficiency:
    formula: "(actual / target) * 100"
    parameters:
      actual: "production_qty"
      target: "target_qty"
    constants:
      max_efficiency: "MAX_EFF"

constants:
  MAX_EFF: 95.0

shift_mappings:
  "A": "Day Shift"
  "B": "Night Shift"
  "C": "General Shift"

precision_defaults:
  production_qty: 2
  efficiency: 1
```

### Advanced Configuration Features

#### 1. Multiple File Loading

```python
from report_manager import ConfigLoader

# Load from multiple files with merging
config = ConfigLoader.from_multiple_files(
    "base_config.yaml",
    "department_config.yaml",
    "formulas_config.json"
)

# Load from directory
config = ConfigLoader.from_directory("config/")

# Mixed sources (files + dictionaries)
override_config = {"precision_defaults": {"new_field": 3}}
config = ConfigLoader.from_mixed_sources(
    "base_config.yaml",
    override_config,
    "additional_config.json"
)
```

#### 2. Configuration Inheritance

```yaml
# base_config.yaml
departments:
  base:
    mandatory_columns:
      - "date"
      - "shift_id"
    default_grouping_columns:
      - "machine_name"

# specific_config.yaml  
departments:
  ringframe:
    # Inherits from base and adds specific columns
    product_column: "count_ne"
    mandatory_columns:
      - "lot_number"  # Merged with base
```

#### 3. Column Grouping Types

```yaml
column_definitions:
  # Sum aggregation
  production_qty:
    grouping_type: "aggregation"
  
  # Average calculation
  efficiency:
    grouping_type: "average"
  
  # Count unique values
  lot_count:
    grouping_type: "counting"
  
  # Simple count
  machine_count:
    grouping_type: "simple_counting"
  
  # Take first value in group
  shift_start_time:
    grouping_type: "first_value"
  
  # Group by this column
  department:
    grouping_type: "grouping"
```

## Report Builders

### Base Builder Architecture

All report builders inherit from `BaseReportBuilder` which provides:

- Data validation and preprocessing
- Column aggregation and grouping
- Formula calculation engine
- Sorting and formatting
- Summary calculation

### Available Builders

#### 1. DaywiseReportBuilder

Generates daily reports with day-wise sections.

**Output Structure:**
```json
{
  "report_type": "daywise",
  "sections": [
    {
      "title": "01 Jan 2024",
      "date": "2024-01-01",
      "subsections": [
        {
          "records": [...]
        }
      ],
      "summary_label": "01 Jan 2024 summary",
      "summary": {...}
    }
  ],
  "summary_label": "overall summary",
  "summary": {...},
  "column_header_mapping": {...}
}
```

#### 2. ShiftwiseReportBuilder

Generates shift-based reports grouped by days.

**Output Structure:**
```json
{
  "report_type": "shiftwise",
  "sections": [
    {
      "title": "01 Jan 2024",
      "date": "2024-01-01",
      "subsections": [
        {
          "title": "Day Shift",
          "shift_id": 1,
          "records": [...],
          "summary": {...}
        }
      ],
      "summary": {...}
    }
  ]
}
```

#### 3. MonthwiseReportBuilder

Generates monthly aggregated reports.

#### 4. WeekwiseReportBuilder

Generates weekly reports with automatic week calculation.

#### 5. InstantaneousReportBuilder

Generates real-time reports without time-based grouping.

### Custom Builder Development

```python
from report_manager.builders.base import BaseReportBuilder
from typing import Dict, Any

class CustomReportBuilder(BaseReportBuilder):
    def prepare_response(self) -> Dict[str, Any]:
        # Custom aggregation logic
        summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )
        
        # Custom grouping logic
        records = (
            self.group_data(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
            .pipe(self.sort_df)
            .to_dicts()
        )
        
        return {
            "report_type": "custom",
            "data": records,
            "summary": summary,
            "column_header_mapping": self.column_mappings
        }

# Register with manager
manager = ReportManager()
manager.register_builder("custom", CustomReportBuilder)
```

## Usage Examples

### Example 1: Production Report with Formulas

```python
import polars as pl
from report_manager import ReportManager, ReportConfig, FormulaConfig, ColumnConfig

# Sample production data
data = pl.DataFrame({
    "date": ["2024-01-01"] * 4,
    "shift_id": [1, 1, 2, 2],
    "platform_shift_id": ["A", "A", "B", "B"],
    "lot_number": ["LOT001", "LOT002", "LOT001", "LOT002"],
    "asset_id": ["M001", "M002", "M001", "M002"],
    "machine_name": ["Ring Frame 1", "Ring Frame 2", "Ring Frame 1", "Ring Frame 2"],
    "actual_production": [100, 120, 90, 110],
    "target_production": [110, 130, 100, 120],
    "running_hours": [8, 8, 8, 8],
    "count_ne": ["20/1", "30/1", "20/1", "30/1"]
})

# Configure with formulas
config = ReportConfig(
    departments={
        "ringframe": {
            "product_column": "count_ne",
            "mandatory_columns": ["date", "lot_number", "asset_id"]
        }
    },
    column_definitions={
        "actual_production": ColumnConfig(
            name="Actual Production",
            unit="Kg",
            grouping_type="aggregation",
            precision=2
        ),
        "efficiency": ColumnConfig(
            name="Efficiency",
            unit="%",
            precision=1
        )
    },
    formulas={
        "efficiency": FormulaConfig(
            formula="(actual / target) * 100",
            parameters={
                "actual": "actual_production",
                "target": "target_production"
            }
        )
    },
    constants={"max_efficiency": 95.0}
)

manager = ReportManager(config)

# Generate shiftwise report
filter_params = ReportFilter(
    department_id="ringframe",
    report_type="shiftwise",
    category="countwise"
)

report = manager.generate_report(
    data_frame=data,
    filter_params=filter_params
)
```

### Example 2: Multi-Department Configuration

```python
# Multi-department configuration
config = ReportConfig(
    departments={
        "ringframe": {
            "product_column": "count_ne",
            "mandatory_columns": ["date", "lot_number", "asset_id"]
        },
        "speedframe": {
            "product_column": "roving_count",
            "mandatory_columns": ["date", "lot_number", "asset_id"]
        },
        "carding": {
            "product_column": "hank_ne",
            "mandatory_columns": ["date", "lot_number", "asset_id"]
        }
    },
    column_definitions={
        "count_ne": ColumnConfig(name="Count", unit="Ne"),
        "roving_count": ColumnConfig(name="Roving Count", unit="Ne"),
        "hank_ne": ColumnConfig(name="Hank", unit="Ne")
    }
)

# Use same data for different departments
ringframe_report = manager.generate_report(
    data_frame=ringframe_data,
    filter_params=ReportFilter(
        department_id="ringframe",
        report_type="daywise",
        category="countwise"
    )
)

speedframe_report = manager.generate_report(
    data_frame=speedframe_data,
    filter_params=ReportFilter(
        department_id="speedframe",
        report_type="daywise",
        category="hankwise"
    )
)
```

### Example 3: Complex Aggregations

```python
# Complex aggregation example
report = manager.generate_report(
    data_frame=data,
    filter_params=filter_params,
    
    # Different column types
    aggregation_columns={"production_qty", "waste_qty"},
    average_columns={"efficiency", "speed"},
    counting_columns={"lot_number", "operator_id"},  # Count unique
    simple_counting_columns={"defect_count"},        # Simple count
    first_value_columns={"shift_start_time", "supervisor"},
    
    # Custom column mappings
    column_mappings={
        "production_qty": {
            "name": "Production",
            "unit": "Kg",
            "sort_order": 1
        },
        "efficiency": {
            "name": "Efficiency",
            "unit": "%",
            "sort_order": 2
        }
    },
    
    # Summary columns
    summary_columns={"production_qty", "efficiency", "waste_qty"}
)
```

## Advanced Features

### 1. Formula Engine

The library includes a powerful formula engine for calculated columns:

#### Supported Operations
- Basic arithmetic: `+`, `-`, `*`, `/`
- Built-in functions: `abs()`, `min()`, `max()`, `round()`, `pow()`
- Constants and parameters

#### Formula Examples

```yaml
formulas:
  # Simple efficiency calculation
  efficiency:
    formula: "(actual / target) * 100"
    parameters:
      actual: "actual_production"
      target: "target_production"
  
  # Complex formula with constants
  adjusted_efficiency:
    formula: "min(efficiency * adjustment_factor, max_efficiency)"
    parameters:
      efficiency: "raw_efficiency"
    constants:
      adjustment_factor: "ADJ_FACTOR"
      max_efficiency: "MAX_EFF"
  
  # Conditional logic
  performance_grade:
    formula: "90 if efficiency >= 85 else (70 if efficiency >= 70 else 50)"
    parameters:
      efficiency: "efficiency"
```

### 2. Dynamic Column Configuration

```python
# Runtime column configuration
dynamic_config = {
    "new_metric": {
        "name": "New Metric",
        "unit": "Units",
        "grouping_type": "aggregation"
    }
}

# Merge with existing config
updated_config = ConfigLoader.merge_configs(base_config, {
    "column_definitions": dynamic_config
})
```

### 3. Data Validation

The library provides comprehensive data validation:

```python
from report_manager.exceptions import DataValidationError

try:
    report = manager.generate_report(data_frame=invalid_data)
except DataValidationError as e:
    print(f"Data validation failed: {e}")
```

**Validation Checks:**
- DataFrame not empty
- Required columns present
- Date format validation
- Numeric column validation
- Formula parameter validation

### 4. Performance Optimization

#### Polars Integration
- Lazy evaluation for large datasets
- Efficient memory usage
- Vectorized operations

#### Caching
- LRU cache for department validation
- Configuration caching
- Builder instance reuse

```python
# Enable lazy evaluation for large datasets
data_lazy = pl.scan_csv("large_dataset.csv")
data_processed = data_lazy.filter(pl.col("date") >= "2024-01-01")

report = manager.generate_report(
    data_frame=data_processed.collect(),
    filter_params=filter_params
)
```

## API Reference

### ReportManager

#### Constructor
```python
ReportManager(config: Optional[ReportConfig] = None)
```

#### Methods

##### generate_report()
```python
generate_report(
    data_frame: pl.DataFrame,
    filter_params: Optional[ReportFilter] = None,
    grouping_columns: Optional[Set[str]] = None,
    aggregation_columns: Optional[Set[str]] = None,
    average_columns: Optional[Set[str]] = None,
    counting_columns: Optional[Set[str]] = None,
    simple_counting_columns: Optional[Set[str]] = None,
    first_value_columns: Optional[Set[str]] = None,
    column_mappings: Optional[Dict[str, Any]] = None,
    summary_columns: Optional[Set[str]] = None,
    **kwargs
) -> Dict[str, Any]
```

**Parameters:**
- `data_frame`: Input Polars DataFrame
- `filter_params`: Report generation parameters
- `*_columns`: Column grouping specifications
- `column_mappings`: Display name and formatting mappings
- `summary_columns`: Columns to include in summaries
- `**kwargs`: Additional builder-specific parameters

**Returns:** Generated report as dictionary

##### register_builder()
```python
register_builder(
    report_type: str,
    builder_class: Union[str, Type[BaseReportBuilder]]
)
```

Register a custom report builder.

##### get_available_report_types()
```python
get_available_report_types() -> List[str]
```

Get list of registered report types.

##### get_department_config()
```python
get_department_config(department_id: str) -> Optional[Dict[str, Any]]
```

Get configuration for a specific department.

### ReportFilter

#### Constructor
```python
ReportFilter(
    department_id: Optional[str] = None,
    report_type: ReportType,
    category: ReportCategory,
    metrics_type: Optional[str] = None,
    is_instantaneous: bool = False
)
```

### ReportConfig

#### Constructor
```python
ReportConfig(
    departments: Dict[str, DepartmentConfig] = {},
    report_types: Dict[str, ReportBuilderConfig] = {},
    column_definitions: Dict[str, ColumnConfig] = {},
    formulas: Dict[str, FormulaConfig] = {},
    **kwargs
)
```

#### Methods

##### get_columns_by_grouping_type()
```python
get_columns_by_grouping_type(grouping_type: GroupingType) -> List[str]
```

##### get_precision_defaults()
```python
get_precision_defaults() -> Dict[str, int]
```

##### get_summary_columns()
```python
get_summary_columns() -> Set[str]
```

### ConfigLoader

#### Static Methods

##### from_yaml()
```python
@staticmethod
from_yaml(yaml_path: Union[str, Path]) -> ReportConfig
```

##### from_json()
```python
@staticmethod
from_json(json_path: Union[str, Path]) -> ReportConfig
```

##### from_multiple_files()
```python
@staticmethod
from_multiple_files(
    *file_paths: Union[str, Path],
    merge_strategy: str = "deep"
) -> ReportConfig
```

##### from_directory()
```python
@staticmethod
from_directory(
    directory_path: Union[str, Path],
    pattern: str = "*.{yaml,yml,json}",
    merge_strategy: str = "deep",
    sort_files: bool = True
) -> ReportConfig
```

## Error Handling

### Exception Hierarchy

```python
ReportManagerException
├── ReportConfigurationError      # Configuration issues
├── ReportBuilderNotFoundError    # Missing builder
├── DataValidationError          # Data validation failures
└── FormulaCalculationError      # Formula calculation errors
```

### Error Handling Examples

```python
from report_manager.exceptions import (
    ReportConfigurationError,
    DataValidationError,
    FormulaCalculationError
)

try:
    report = manager.generate_report(
        data_frame=data,
        filter_params=filter_params
    )
except ReportConfigurationError as e:
    print(f"Configuration error: {e}")
    # Handle configuration issues
    
except DataValidationError as e:
    print(f"Data validation failed: {e}")
    # Handle data issues
    
except FormulaCalculationError as e:
    print(f"Formula calculation failed: {e}")
    # Handle formula errors
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

### Common Error Scenarios

#### 1. Missing Required Columns
```python
# Error: Required columns missing: ['date', 'lot_number']
DataValidationError: Required columns missing: ['date', 'lot_number']
```

#### 2. Invalid Department Configuration
```python
# Error: Department 'invalid_dept' not configured
ReportConfigurationError: Department 'invalid_dept' not configured
```

#### 3. Formula Calculation Errors
```python
# Error: Error calculating formula 'efficiency': division by zero
FormulaCalculationError: Error calculating formula 'efficiency': division by zero
```

## Best Practices

### 1. Configuration Management

**DO:**
```python
# Use structured configuration files
config = ConfigLoader.from_yaml("production_config.yaml")

# Separate concerns with multiple config files
config = ConfigLoader.from_multiple_files(
    "base_config.yaml",        # Base settings
    "departments.yaml",        # Department-specific
    "formulas.yaml"           # Formula definitions
)

# Use environment-specific configurations
env = os.getenv("ENVIRONMENT", "development")
config = ConfigLoader.from_yaml(f"config/{env}.yaml")
```

**DON'T:**
```python
# Avoid hardcoded configurations
config = ReportConfig(
    departments={"dept1": {"product_column": "hardcoded_column"}}
)
```

### 2. Data Preparation

**DO:**
```python
# Validate data before processing
if data.is_empty():
    raise ValueError("Empty dataset")

# Ensure required columns exist
required_columns = ["date", "shift_id", "lot_number"]
missing = [col for col in required_columns if col not in data.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# Use proper data types
data = data.with_columns([
    pl.col("date").str.strptime(pl.Date, "%Y-%m-%d"),
    pl.col("production_qty").cast(pl.Float64)
])
```

**DON'T:**
```python
# Don't assume data structure
report = manager.generate_report(unchecked_data, filter_params)
```

### 3. Error Handling

**DO:**
```python
# Use specific exception handling
try:
    report = manager.generate_report(data, filter_params)
except DataValidationError as e:
    logger.error(f"Data validation failed: {e}")
    return {"error": "Invalid data", "details": str(e)}
except ReportConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    return {"error": "Configuration issue", "details": str(e)}
```

**DON'T:**
```python
# Don't use broad exception handling
try:
    report = manager.generate_report(data, filter_params)
except Exception as e:
    print("Something went wrong")
```

### 4. Performance Optimization

**DO:**
```python
# Use lazy evaluation for large datasets
data_lazy = pl.scan_parquet("large_dataset.parquet")
filtered_data = data_lazy.filter(
    pl.col("date").is_between("2024-01-01", "2024-01-31")
)
report = manager.generate_report(filtered_data.collect(), filter_params)

# Reuse manager instances
manager = ReportManager(config)
for department in departments:
    filter_params.department_id = department
    report = manager.generate_report(data, filter_params)
```

**DON'T:**
```python
# Don't create new managers for each report
for department in departments:
    manager = ReportManager(config)  # Inefficient
    report = manager.generate_report(data, filter_params)
```

### 5. Configuration Best Practices

#### File Organization
```
config/
├── base.yaml              # Base configuration
├── departments/
│   ├── ringframe.yaml     # Department-specific
│   ├── speedframe.yaml
│   └── carding.yaml
├── formulas/
│   ├── efficiency.yaml    # Formula definitions
│   └── quality.yaml
└── environments/
    ├── development.yaml   # Environment-specific
    ├── staging.yaml
    └── production.yaml
```

#### Modular Configuration
```yaml
# base.yaml
defaults:
  precision: 2
  mandatory_columns:
    - "date"
    - "shift_id"
    - "asset_id"

# departments/ringframe.yaml
department:
  ringframe:
    product_column: "count_ne"
    extends: "defaults"
    additional_columns:
      - "lot_number"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Memory Issues with Large Datasets

**Problem:** Out of memory errors with large datasets
```python
MemoryError: Unable to allocate array
```

**Solution:**
```python
# Use lazy evaluation and streaming
data_stream = pl.scan_csv("large_file.csv")
data_filtered = data_stream.filter(pl.col("date") >= "2024-01-01")

# Process in chunks
chunk_size = 10000
for chunk in data_filtered.iter_slices(chunk_size):
    report_chunk = manager.generate_report(chunk, filter_params)
    # Process chunk results
```

#### 2. Formula Calculation Errors

**Problem:** Division by zero in formulas
```python
FormulaCalculationError: Error calculating formula 'efficiency': division by zero
```

**Solution:**
```python
# Use safe division in formulas
formulas:
  efficiency:
    formula: "(actual / target * 100) if target > 0 else 0"
    parameters:
      actual: "actual_production"
      target: "target_production"

# Or handle in data preprocessing
data = data.with_columns([
    pl.when(pl.col("target_production") == 0)
    .then(pl.lit(1))  # Avoid division by zero
    .otherwise(pl.col("target_production"))
    .alias("target_production")
])
```

#### 3. Configuration Loading Issues

**Problem:** Configuration file not found
```python
FileNotFoundError: Configuration file not found: config.yaml
```

**Solution:**
```python
import os
from pathlib import Path

# Use absolute paths
config_path = Path(__file__).parent / "config" / "production.yaml"
if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")

config = ConfigLoader.from_yaml(config_path)

# Or use environment variables
config_path = os.getenv("REPORT_CONFIG", "config/default.yaml")
config = ConfigLoader.from_yaml(config_path)
```

#### 4. Column Mapping Issues

**Problem:** Columns not appearing in report
```python
# Columns defined but not showing in output
```

**Solution:**
```python
# Ensure column mappings are properly defined
column_mappings = {
    "production_qty": {
        "name": "Production Quantity",
        "unit": "Kg",
        "sort_order": 1
    },
    "efficiency": {
        "name": "Efficiency %",
        "unit": "%",
        "sort_order": 2
    }
}

# Verify columns exist in data
missing_cols = [col for col in column_mappings.keys() 
                if col not in data.columns]
if missing_cols:
    print(f"Warning: Mapped columns not in data: {missing_cols}")

# Check if columns are in summary_columns for summary inclusion
summary_columns = {"production_qty", "efficiency"}
```

#### 5. Date Parsing Issues

**Problem:** Date columns not recognized
```python
DataValidationError: Error processing date column: invalid date format
```

**Solution:**
```python
# Standardize date formats before processing
data = data.with_columns([
    pl.col("date").str.strptime(pl.Date, "%Y-%m-%d", strict=False)
])

# Handle multiple date formats
def parse_flexible_date(date_str):
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"]
    for fmt in formats:
        try:
            return pl.col("date").str.strptime(pl.Date, fmt)
        except:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")

# Or use Polars' flexible parsing
data = data.with_columns([
    pl.col("date").str.to_date()
])
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("report_manager")

# Generate report with debug info
try:
    report = manager.generate_report(data, filter_params)
    logger.info(f"Report generated successfully with {len(report['sections'])} sections")
except Exception as e:
    logger.error(f"Report generation failed: {e}", exc_info=True)
```

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

# Monitor report generation
@monitor_performance
def generate_monitored_report(manager, data, filter_params):
    return manager.generate_report(data, filter_params)

report = generate_monitored_report(manager, data, filter_params)
```

## Advanced Integration Examples

### 1. Flask Web API Integration

```python
from flask import Flask, request, jsonify
from report_manager import ReportManager, ReportFilter, ConfigLoader
import polars as pl

app = Flask(__name__)

# Initialize report manager
config = ConfigLoader.from_yaml("config/production.yaml")
manager = ReportManager(config)

@app.route('/api/reports', methods=['POST'])
def generate_report_api():
    try:
        # Parse request data
        request_data = request.get_json()
        
        # Create DataFrame from request data
        data = pl.DataFrame(request_data['data'])
        
        # Create filter parameters
        filter_params = ReportFilter(
            department_id=request_data['department_id'],
            report_type=request_data['report_type'],
            category=request_data['category']
        )
        
        # Generate report
        report = manager.generate_report(
            data_frame=data,
            filter_params=filter_params,
            **request_data.get('options', {})
        )
        
        return jsonify({
            'status': 'success',
            'report': report
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
```

### 2. Celery Task Integration

```python
from celery import Celery
from report_manager import ReportManager, ReportFilter, ConfigLoader
import polars as pl

app = Celery('report_tasks')

# Initialize report manager
config = ConfigLoader.from_yaml("config/production.yaml")
manager = ReportManager(config)

@app.task
def generate_report_task(data_dict, filter_params_dict, options=None):
    """Async report generation task."""
    try:
        # Convert data back to DataFrame
        data = pl.DataFrame(data_dict)
        
        # Create filter parameters
        filter_params = ReportFilter(**filter_params_dict)
        
        # Generate report
        report = manager.generate_report(
            data_frame=data,
            filter_params=filter_params,
            **(options or {})
        )
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Usage
result = generate_report_task.delay(
    data_dict=data.to_dict(),
    filter_params_dict={
        'department_id': 'ringframe',
        'report_type': 'daywise',
        'category': 'countwise'
    }
)
```

### 3. Pandas Integration

```python
import pandas as pd
import polars as pl
from report_manager import ReportManager

def pandas_to_report(df_pandas, filter_params):
    """Convert Pandas DataFrame to report using ReportManager."""
    
    # Convert Pandas to Polars
    df_polars = pl.from_pandas(df_pandas)
    
    # Generate report
    manager = ReportManager()
    report = manager.generate_report(df_polars, filter_params)
    
    return report

# Usage with existing Pandas workflow
df_pandas = pd.read_csv("production_data.csv")
df_pandas['date'] = pd.to_datetime(df_pandas['date'])

report = pandas_to_report(df_pandas, filter_params)
```

### 4. Database Integration

```python
import polars as pl
from sqlalchemy import create_engine
from report_manager import ReportManager, ReportFilter

class DatabaseReportGenerator:
    def __init__(self, db_url, config_path):
        self.engine = create_engine(db_url)
        config = ConfigLoader.from_yaml(config_path)
        self.manager = ReportManager(config)
    
    def generate_from_query(self, query, filter_params):
        """Generate report from SQL query."""
        
        # Read data using Polars
        data = pl.read_database(query, self.engine)
        
        # Generate report
        return self.manager.generate_report(data, filter_params)
    
    def generate_production_report(self, start_date, end_date, department):
        """Generate production report for date range."""
        
        query = f"""
        SELECT 
            date,
            shift_id,
            platform_shift_id,
            lot_number,
            asset_id,
            machine_name,
            production_qty,
            target_qty,
            count_ne
        FROM production_data 
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND department_id = '{department}'
        """
        
        filter_params = ReportFilter(
            department_id=department,
            report_type='daywise',
            category='countwise'
        )
        
        return self.generate_from_query(query, filter_params)

# Usage
db_generator = DatabaseReportGenerator(
    "postgresql://user:pass@localhost/production",
    "config/production.yaml"
)

report = db_generator.generate_production_report(
    "2024-01-01", "2024-01-31", "ringframe"
)
```

## Testing Framework

### Unit Testing Examples

```python
import unittest
import polars as pl
from report_manager import ReportManager, ReportFilter, ReportConfig
from report_manager.exceptions import DataValidationError

class TestReportManager(unittest.TestCase):
    
    def setUp(self):
        """Setup test fixtures."""
        self.config = ReportConfig(
            departments={
                "test_dept": {
                    "product_column": "count_ne",
                    "mandatory_columns": ["date", "lot_number"]
                }
            }
        )
        self.manager = ReportManager(self.config)
        
        self.sample_data = pl.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            "shift_id": [1, 2],
            "platform_shift_id": ["A", "B"],
            "lot_number": ["LOT001", "LOT002"],
            "asset_id": ["M001", "M002"],
            "machine_name": ["Machine1", "Machine2"],
            "production_qty": [100, 150],
            "count_ne": ["20/1", "30/1"]
        })
        
        self.filter_params = ReportFilter(
            department_id="test_dept",
            report_type="daywise",
            category="countwise"
        )
    
    def test_basic_report_generation(self):
        """Test basic report generation."""
        report = self.manager.generate_report(
            self.sample_data, 
            self.filter_params
        )
        
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report_type'], 'daywise')
        self.assertIn('sections', report)
        self.assertIn('summary', report)
    
    def test_empty_dataframe_validation(self):
        """Test validation with empty DataFrame."""
        empty_df = pl.DataFrame()
        
        with self.assertRaises(ValueError):
            self.manager.generate_report(empty_df, self.filter_params)
    
    def test_missing_columns_validation(self):
        """Test validation with missing required columns."""
        incomplete_data = self.sample_data.select(["date", "shift_id"])
        
        with self.assertRaises(DataValidationError):
            self.manager.generate_report(incomplete_data, self.filter_params)
    
    def test_custom_aggregations(self):
        """Test custom aggregation configurations."""
        report = self.manager.generate_report(
            self.sample_data,
            self.filter_params,
            aggregation_columns={"production_qty"}
        )
        
        # Verify aggregation was applied
        total_production = sum(self.sample_data["production_qty"])
        self.assertEqual(
            report['summary']['production_qty'], 
            total_production
        )

class TestConfigLoader(unittest.TestCase):
    
    def test_yaml_loading(self):
        """Test YAML configuration loading."""
        # Create temporary YAML file
        config_content = """
        departments:
          test_dept:
            product_column: "count_ne"
        """
        
        with open("test_config.yaml", "w") as f:
            f.write(config_content)
        
        try:
            config = ConfigLoader.from_yaml("test_config.yaml")
            self.assertIn("test_dept", config.departments)
        finally:
            os.remove("test_config.yaml")

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```python
import pytest
import polars as pl
from report_manager import ReportManager, ConfigLoader

@pytest.fixture
def sample_production_data():
    """Sample production data fixture."""
    return pl.DataFrame({
        "date": ["2024-01-01"] * 4 + ["2024-01-02"] * 4,
        "shift_id": [1, 1, 2, 2] * 2,
        "platform_shift_id": ["A", "A", "B", "B"] * 2,
        "lot_number": ["LOT001", "LOT002"] * 4,
        "asset_id": ["M001", "M002"] * 4,
        "machine_name": ["Machine1", "Machine2"] * 4,
        "production_qty": [100, 120, 90, 110, 105, 125, 95, 115],
        "target_qty": [110, 130, 100, 120, 115, 135, 105, 125],
        "count_ne": ["20/1", "30/1"] * 4
    })

@pytest.fixture
def production_config():
    """Production configuration fixture."""
    return ConfigLoader.from_yaml("config/test_config.yaml")

@pytest.fixture
def report_manager(production_config):
    """Report manager fixture."""
    return ReportManager(production_config)

def test_daywise_report_structure(report_manager, sample_production_data):
    """Test daywise report structure and content."""
    filter_params = ReportFilter(
        department_id="ringframe",
        report_type="daywise",
        category="countwise"
    )
    
    report = report_manager.generate_report(
        sample_production_data, 
        filter_params
    )
    
    # Test structure
    assert "sections" in report
    assert len(report["sections"]) == 2  # 2 days
    assert "summary" in report
    
    # Test section structure
    for section in report["sections"]:
        assert "title" in section
        assert "date" in section
        assert "subsections" in section
        assert "summary" in section

def test_formula_calculations(report_manager, sample_production_data):
    """Test formula calculations in reports."""
    # Add formula configuration
    config_with_formulas = ReportConfig(
        departments={
            "ringframe": {
                "product_column": "count_ne",
                "mandatory_columns": ["date", "lot_number"]
            }
        },
        formulas={
            "efficiency": {
                "formula": "(actual / target) * 100",
                "parameters": {
                    "actual": "production_qty",
                    "target": "target_qty"
                }
            }
        }
    )
    
    manager_with_formulas = ReportManager(config_with_formulas)
    
    filter_params = ReportFilter(
        department_id="ringframe",
        report_type="daywise",
        category="countwise"
    )
    
    report = manager_with_formulas.generate_report(
        sample_production_data,
        filter_params
    )
    
    # Verify efficiency calculation exists
    assert "efficiency" in report["summary"]
    assert isinstance(report["summary"]["efficiency"], (int, float))

@pytest.mark.parametrize("report_type", ["daywise", "weekwise", "monthwise", "shiftwise"])
def test_all_report_types(report_manager, sample_production_data, report_type):
    """Test all report types generate successfully."""
    filter_params = ReportFilter(
        department_id="ringframe",
        report_type=report_type,
        category="countwise"
    )
    
    report = report_manager.generate_report(
        sample_production_data,
        filter_params
    )
    
    assert report["report_type"] == report_type
    assert "sections" in report or "data" in report
    assert "summary" in report
```

## Deployment Guide

### Production Deployment

#### 1. Environment Setup

```bash
# Create virtual environment
python -m venv report_manager_env
source report_manager_env/bin/activate  # Linux/Mac
# or
report_manager_env\Scripts\activate  # Windows

# Install production dependencies
pip install -r requirements.txt

# Install with production extras
pip install -e ".[prod]"
```

#### 2. Configuration Management

```python
# config/production.py
import os
from report_manager import ConfigLoader

def get_production_config():
    """Get production configuration with environment overrides."""
    
    base_config = ConfigLoader.from_yaml("config/base.yaml")
    
    # Environment-specific overrides
    env_overrides = {
        "constants": {
            "MAX_EFFICIENCY": float(os.getenv("MAX_EFFICIENCY", "95.0")),
            "TARGET_UTILIZATION": float(os.getenv("TARGET_UTILIZATION", "85.0"))
        },
        "precision_defaults": {
            col: int(os.getenv(f"PRECISION_{col.upper()}", "2"))
            for col in ["production_qty", "efficiency", "utilization"]
        }
    }
    
    return ConfigLoader.merge_configs(base_config, env_overrides)
```

#### 3. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Set environment variables
ENV PYTHONPATH=/app
ENV REPORT_CONFIG_PATH=/app/config/production.yaml

# Expose port for web API (if applicable)
EXPOSE 8000

# Run command
CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  report-manager:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/production
      - REDIS_URL=redis://redis:6379/0
      - MAX_EFFICIENCY=95.0
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=production
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine

volumes:
  postgres_data:
```

#### 4. Monitoring and Logging

```python
# monitoring.py
import logging
import time
from functools import wraps
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REPORT_REQUESTS = Counter('report_requests_total', 'Total report requests', ['department', 'report_type'])
REPORT_DURATION = Histogram('report_generation_seconds', 'Report generation time')
REPORT_ERRORS = Counter('report_errors_total', 'Total report errors', ['error_type'])

def setup_logging():
    """Setup production logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/app/logs/report_manager.log'),
            logging.StreamHandler()
        ]
    )

def monitor_report_generation(func):
    """Decorator to monitor report generation."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # Extract filter params for metrics
            filter_params = kwargs.get('filter_params')
            if filter_params:
                REPORT_REQUESTS.labels(
                    department=filter_params.department_id,
                    report_type=filter_params.report_type
                ).inc()
            
            result = func(*args, **kwargs)
            
            # Record success metrics
            duration = time.time() - start_time
            REPORT_DURATION.observe(duration)
            
            return result
            
        except Exception as e:
            # Record error metrics
            REPORT_ERRORS.labels(error_type=type(e).__name__).inc()
            raise
    
    return wrapper
```

### Performance Tuning

#### 1. Memory Optimization

```python
# config/performance.py
PERFORMANCE_CONFIG = {
    # Polars settings
    "polars": {
        "streaming": True,  # Enable streaming for large datasets
        "lazy": True,       # Use lazy evaluation
        "thread_pool_size": 4
    },
    
    # Caching settings
    "cache": {
        "enable_lru_cache": True,
        "max_cache_size": 128,
        "ttl_seconds": 3600
    },
    
    # Batch processing
    "batch": {
        "chunk_size": 10000,
        "max_memory_mb": 1024
    }
}

def optimize_dataframe_processing(df, chunk_size=10000):
    """Process DataFrame in optimized chunks."""
    if len(df) <= chunk_size:
        return df
    
    # Process in chunks for large datasets
    chunks = []
    for start_idx in range(0, len(df), chunk_size):
        end_idx = min(start_idx + chunk_size, len(df))
        chunk = df.slice(start_idx, end_idx - start_idx)
        chunks.append(chunk)
    
    return pl.concat(chunks)
```

#### 2. Database Query Optimization

```python
# optimized_queries.py
OPTIMIZED_QUERIES = {
    "production_summary": """
        SELECT 
            date,
            department_id,
            SUM(production_qty) as total_production,
            AVG(efficiency) as avg_efficiency,
            COUNT(DISTINCT lot_number) as lot_count
        FROM production_data 
        WHERE date BETWEEN :start_date AND :end_date
        GROUP BY date, department_id
        ORDER BY date
    """,
    
    "detailed_production": """
        SELECT *
        FROM production_data 
        WHERE date BETWEEN :start_date AND :end_date
        AND department_id = :department_id
        ORDER BY date, shift_id, asset_id
    """
}

def get_optimized_data(engine, query_name, **params):
    """Get data using optimized queries."""
    query = OPTIMIZED_QUERIES[query_name]
    return pl.read_database(query, engine, params=params)
```

This comprehensive documentation covers all aspects of the Report Manager Core library, from basic usage to advanced deployment scenarios. The library is well-designed for industrial IoT applications with its flexible configuration system, powerful aggregation capabilities, and extensible architecture.
    