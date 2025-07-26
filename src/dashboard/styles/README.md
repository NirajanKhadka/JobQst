# Unified Dashboard CSS System

This directory contains the unified CSS system for the AutoJobAgent Dashboard, providing consistent styling across all dashboard components and interfaces.

## Overview

The unified CSS system centralizes all styling for:
- **Streamlit Dashboard** (`unified_dashboard.py`)
- **HTML Dashboard** (`dashboard.html`)
- **All Dashboard Components** (orchestration, logging, etc.)

## Files

### `unified_dashboard_styles.css`
The main CSS file containing:
- **CSS Variables**: Centralized color palette, spacing, shadows, etc.
- **Base Styles**: Reset, typography, layout foundations
- **Component Styles**: Cards, buttons, tables, forms, etc.
- **Utility Classes**: Status indicators, animations, responsive design
- **Theme System**: Dark theme with consistent color scheme

## CSS Architecture

### 1. CSS Variables (Design Tokens)
All colors, spacing, shadows, and other design properties are defined as CSS variables:

```css
:root {
    /* Colors */
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: #334155;
    --text-primary: #f1f5f9;
    --accent-primary: #3b82f6;
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    
    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
}
```

### 2. Component Classes
Reusable component classes for consistent styling:

```css
.card-base {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-md);
    transition: var(--transition-normal);
}

.btn-base {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    font-weight: 500;
    transition: var(--transition-normal);
}
```

### 3. Utility Classes
Helper classes for common styling needs:

```css
.status-running { color: var(--success); }
.status-stopped { color: var(--error); }
.fade-in { animation: fadeIn 0.5s ease-out; }
.pulse { animation: pulse 2s infinite; }
```

## Usage

### In Streamlit Components
```python
from src.dashboard.components.dashboard_styling import DashboardStyling

# Apply unified styles
DashboardStyling.apply_global_styles()

# Use utility methods
status_badge = DashboardStyling.create_status_badge("running", "Active")
```

### In HTML Templates
```html
<link rel="stylesheet" href="../styles/unified_dashboard_styles.css">

<!-- Use CSS classes -->
<div class="card-base">
    <button class="btn-primary">Action</button>
    <span class="status-badge running">Running</span>
</div>
```

### In Component Files
Components automatically inherit the unified styles when the main dashboard loads the CSS.

## Color Palette

### Primary Colors
- **Background Primary**: `#0f172a` (Dark navy)
- **Background Secondary**: `#1e293b` (Lighter navy)
- **Background Card**: `#334155` (Card background)
- **Text Primary**: `#f1f5f9` (Light gray)
- **Accent Primary**: `#3b82f6` (Blue)

### Status Colors
- **Success**: `#10b981` (Green)
- **Warning**: `#f59e0b` (Orange)
- **Error**: `#ef4444` (Red)
- **Info**: `#06b6d4` (Cyan)

### Usage Guidelines
- Use CSS variables instead of hardcoded colors
- Follow the established color hierarchy
- Maintain sufficient contrast for accessibility

## Component Guidelines

### Cards
```css
.metric-card {
    @extend .card-base;
    /* Additional metric-specific styles */
}
```

### Buttons
```css
.btn-primary {
    @extend .btn-base;
    background: var(--accent-primary);
    color: var(--text-inverse);
}
```

### Status Indicators
```css
.job-badge.applied {
    background: var(--success-bg);
    color: var(--success);
    border: 1px solid var(--success);
}
```

## Responsive Design

The system includes responsive breakpoints:

```css
@media (max-width: 768px) {
    .dashboard-header { padding: var(--spacing-lg); }
    .metric-card { padding: var(--spacing-md); }
}

@media (max-width: 480px) {
    .dashboard-title { font-size: 1.75rem; }
    .metric-value { font-size: 1.75rem; }
}
```

## Accessibility

### Focus States
All interactive elements have proper focus states:
```css
.btn-base:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}
```

### High Contrast Support
```css
@media (prefers-contrast: high) {
    :root {
        --border-color: #ffffff;
        --text-secondary: #ffffff;
    }
}
```

### Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

## Animations

### Available Animations
- **fadeIn**: Smooth entrance animation
- **pulse**: Breathing effect for status indicators
- **slideInRight/Left**: Slide transitions
- **bounceIn**: Attention-grabbing entrance

### Usage
```css
.fade-in { animation: fadeIn 0.5s ease-out; }
.pulse { animation: pulse 2s infinite; }
```

## Maintenance

### Adding New Components
1. Define component-specific variables if needed
2. Create base component class extending existing patterns
3. Add variants for different states/types
4. Include responsive styles
5. Test across both Streamlit and HTML dashboards

### Modifying Colors
1. Update CSS variables in `:root`
2. Test across all components
3. Verify accessibility contrast ratios
4. Update documentation

### Best Practices
- **Use CSS variables** for all colors and spacing
- **Follow naming conventions** (component-property-variant)
- **Test responsiveness** at all breakpoints
- **Maintain accessibility** standards
- **Document changes** in this README

## File Structure

```
src/dashboard/styles/
├── unified_dashboard_styles.css    # Main CSS file
├── README.md                       # This documentation
└── components/                     # Component-specific extensions (future)
```

## Integration Points

### Streamlit Dashboard
- Loaded via `load_unified_css()` function
- Extended by `dashboard_styling.py`
- Applied globally in `unified_dashboard.py`

### HTML Dashboard
- Linked directly in `<head>` section
- Extended by inline `<style>` blocks
- Overrides Tailwind classes where needed

### Components
- Inherit styles automatically
- Can extend with component-specific CSS
- Use utility classes for common patterns

## Future Enhancements

### Planned Features
- **Theme Toggle**: Light/dark mode switching
- **CSS Linting**: Automated style validation
- **Design Tokens**: JSON-based design system
- **Component Library**: Reusable UI components

### Migration Path
- Gradually move inline styles to unified system
- Consolidate duplicate CSS across components
- Standardize naming conventions
- Improve documentation and examples

## Troubleshooting

### Common Issues

**Styles not applying:**
- Check if CSS file path is correct
- Verify CSS variables are defined
- Ensure proper CSS specificity

**Inconsistent colors:**
- Use CSS variables instead of hardcoded values
- Check for conflicting inline styles
- Verify variable names are correct

**Responsive issues:**
- Test at all breakpoints
- Check media query syntax
- Verify mobile-first approach

### Debug Tips
- Use browser dev tools to inspect CSS
- Check for CSS variable inheritance
- Verify file loading in network tab
- Test with different screen sizes

---

**Note**: This unified CSS system requires explicit user request for edits to maintain consistency and prevent conflicts across the dashboard ecosystem.