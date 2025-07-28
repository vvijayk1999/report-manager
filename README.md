# Report Manager Core

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)

A modular, configurable report generation library specifically designed for Industrial IoT (IIoT) applications. Built with performance in mind using Polars for fast data processing and featuring a flexible configuration system for complex report requirements.

## 🚀 Key Features

- **🏗️ Modular Architecture**: Extensible builder pattern with pluggable report types
- **📊 Multiple Report Types**: Daywise, weekwise, monthwise, shiftwise, and instantaneous reports
- **⚙️ Flexible Configuration**: YAML/JSON-based configuration with inheritance and merging
- **🧮 Formula Engine**: Built-in support for calculated columns with formula expressions
- **✅ Data Validation**: Comprehensive input validation and error handling
- **🏭 Industry-Specific**: Optimized for textile/spinning industry with department-specific configurations
- **⚡ High Performance**: Built on Polars for fast data processing

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported Report Types](#supported-report-types)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Requirements

- Python 3.8+
- Polars >= 0.20.10
- Pydantic >= 1.10.13
- PyYAML >= 6.0
- typing-extensions >= 4.0.0

### Install from Source

```bash
git clone <repository-url>
cd report-manager-core
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev,docs]"
```

## ⚡ Quick Start

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

## 📊 Supported Report Types

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

## ⚙️ Configuration

The library supports flexible YAML/JSON-based configuration:

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
  MAX_EFFICIENCY: 95.0

shift_mappings:
  "A": "Day Shift"
  "B": "Night Shift"
  "C": "General Shift"
```

### Loading Configuration

```python
from report_manager import ConfigLoader

# From single file
config = ConfigLoader.from_yaml("config.yaml")

# From multiple files (with merging)
config = ConfigLoader.from_multiple_files(
    "base_config.yaml",
    "department_config.yaml",
    "formulas_config.json"
)

# From directory
config = ConfigLoader.from_directory("config/")
```

## 💡 Usage Examples

### Basic Report Generation

```python
from report_manager import ReportManager, ReportFilter

manager = ReportManager()
filter_params = ReportFilter(
    department_id="ringframe",
    report_type="daywise",
    category="countwise"
)

report = manager.generate_report(data_frame=data, filter_params=filter_params)
```

### With Formula Calculations

```python
from report_manager import ReportConfig, FormulaConfig, ColumnConfig

config = ReportConfig(
    formulas={
        "efficiency": FormulaConfig(
            formula="(actual / target) * 100",
            parameters={
                "actual": "actual_production",
                "target": "target_production"
            }
        )
    },
    column_definitions={
        "efficiency": ColumnConfig(
            name="Efficiency",
            unit="%",
            precision=1
        )
    }
)

manager = ReportManager(config)
report = manager.generate_report(data_frame=data, filter_params=filter_params)
```

### Complex Aggregations

```python
report = manager.generate_report(
    data_frame=data,
    filter_params=filter_params,
    aggregation_columns={"production_qty", "waste_qty"},
    average_columns={"efficiency", "speed"},
    counting_columns={"lot_number", "operator_id"},  # Count unique
    simple_counting_columns={"defect_count"},        # Simple count
    first_value_columns={"shift_start_time", "supervisor"},
    column_mappings={
        "production_qty": {
            "name": "Production",
            "unit": "Kg",
            "sort_order": 1
        }
    }
)
```

## 🔧 Advanced Features

### Formula Engine

The library includes a powerful formula engine for calculated columns:

```yaml
formulas:
  # Simple calculation
  efficiency:
    formula: "(actual / target) * 100"
    parameters:
      actual: "actual_production"
      target: "target_production"
  
  # With constants
  adjusted_efficiency:
    formula: "min(efficiency * adjustment_factor, max_efficiency)"
    parameters:
      efficiency: "raw_efficiency"
    constants:
      adjustment_factor: "ADJ_FACTOR"
      max_efficiency: "MAX_EFF"
```

### Custom Report Builders

```python
from report_manager.builders.base import BaseReportBuilder

class CustomReportBuilder(BaseReportBuilder):
    def prepare_response(self) -> Dict[str, Any]:
        # Custom aggregation logic
        summary = (
            self._calculate_summary(self.df)
            .pipe(self._add_calculated_columns)
            .pipe(self.roundoff)
            .to_dicts()[0]
        )
        
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
manager.register_builder("custom", CustomReportBuilder)
```

### Performance Optimization

```python
# For large datasets, use lazy evaluation
data_lazy = pl.scan_csv("large_dataset.csv")
data_processed = data_lazy.filter(pl.col("date") >= "2024-01-01")

report = manager.generate_report(
    data_frame=data_processed.collect(),
    filter_params=filter_params
)
```

## 📚 API Reference

### ReportManager

Main orchestrator for report generation.

```python
manager = ReportManager(config: Optional[ReportConfig] = None)

# Generate report
report = manager.generate_report(
    data_frame: pl.DataFrame,
    filter_params: Optional[ReportFilter] = None,
    **kwargs
) -> Dict[str, Any]

# Register custom builder
manager.register_builder(report_type: str, builder_class)

# Get available report types
types = manager.get_available_report_types() -> List[str]
```

### ReportFilter

Defines parameters for report generation.

```python
filter_params = ReportFilter(
    department_id: Optional[str] = None,
    report_type: ReportType,
    category: ReportCategory,
    metrics_type: Optional[str] = None,
    is_instantaneous: bool = False
)
```

### ConfigLoader

Utility for loading configurations.

```python
# From file
config = ConfigLoader.from_yaml("config.yaml")
config = ConfigLoader.from_json("config.json")

# From multiple sources
config = ConfigLoader.from_multiple_files("base.yaml", "override.yaml")
config = ConfigLoader.from_directory("config/")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│              Client Code                │
├─────────────────────────────────────────┤
│            ReportManager                │  ← Main entry point
├─────────────────────────────────────────┤
│     Configuration & Filter System       │  ← ReportConfig, ReportFilter
├─────────────────────────────────────────┤
│          Report Builders                │  ← Specific report implementations
├─────────────────────────────────────────┤
│            Base Builder                 │  ← Common functionality
├─────────────────────────────────────────┤
│          Data Processing                │  ← Polars DataFrame operations
└─────────────────────────────────────────┘
```

## 🚨 Error Handling

The library provides comprehensive error handling:

```python
from report_manager.exceptions import (
    ReportConfigurationError,
    DataValidationError,
    FormulaCalculationError
)

try:
    report = manager.generate_report(data, filter_params)
except DataValidationError as e:
    print(f"Data validation failed: {e}")
except ReportConfigurationError as e:
    print(f"Configuration error: {e}")
except FormulaCalculationError as e:
    print(f"Formula calculation failed: {e}")
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=report_manager

# Run specific test file
pytest tests/test_report_manager.py
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd report-manager-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev,docs]"

# Run tests
pytest

# Run linting
flake8 report_manager/
black --check report_manager/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **V Vijay Krishnan** - *Initial work* - [vvijayk1999@gmail.com](mailto:vvijayk1999@gmail.com)

## 🙏 Acknowledgments

- Built with [Polars](https://www.pola.rs/) for high-performance data processing
- Configuration management powered by [Pydantic](https://pydantic-docs.helpmanual.io/)
- Inspired by industrial IoT reporting requirements

## 📞 Support

- 📧 Email: vvijayk1999@gmail.com
- 📖 Documentation: [documentation](https://github.com/vvijayk1999/report-manager/documentation.md)
<!-- - 🐛 Issues: [GitHub Issues](https://github.com/vvijayk1999/report-manager/blob/master/documentation.md) -->

---

⭐ If you find this project useful, please consider giving it a star on GitHub!