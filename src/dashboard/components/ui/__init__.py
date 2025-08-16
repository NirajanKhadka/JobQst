"""
Reusable UI Components Package

This package contains reusable UI components for the dashboard.
Components are designed to be modular, configurable, and consistent
across the entire application.

Components:
- chart_components: Reusable Plotly chart widgets with consistent styling
- status_widgets: Health status, progress bars, metric displays  
- form_components: Standardized inputs, selectors, buttons
- metric_cards: Dashboard KPI cards with animations
"""

from .chart_components import (
    BaseChart, 
    LineChart, 
    BarChart, 
    PieChart, 
    ScatterChart,
    HeatmapChart,
    GaugeChart
)

from .status_widgets import (
    StatusIndicator,
    ProgressBar,
    MetricDisplay,
    HealthStatus,
    AlertBadge,
    CounterWidget
)

from .form_components import (
    FormInput,
    FormSelect,
    FormButton,
    FormCheckbox,
    FormRadio,
    FormTextarea,
    FormDatePicker,
    FormNumberInput
)

from .metric_cards import (
    MetricCard,
    KPICard,
    TrendCard,
    ComparisonCard,
    AnimatedCounter,
    StatusCard
)

__all__ = [
    # Chart Components
    'BaseChart', 'LineChart', 'BarChart', 'PieChart', 'ScatterChart',
    'HeatmapChart', 'GaugeChart',
    
    # Status Widgets
    'StatusIndicator', 'ProgressBar', 'MetricDisplay', 'HealthStatus',
    'AlertBadge', 'CounterWidget',
    
    # Form Components
    'FormInput', 'FormSelect', 'FormButton', 'FormCheckbox', 'FormRadio',
    'FormTextarea', 'FormDatePicker', 'FormNumberInput',
    
    # Metric Cards
    'MetricCard', 'KPICard', 'TrendCard', 'ComparisonCard',
    'AnimatedCounter', 'StatusCard'
]
