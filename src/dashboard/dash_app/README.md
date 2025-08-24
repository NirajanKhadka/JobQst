# JobQst Dash Dashboard

A modern, interactive dashboard for the JobQst automated job discovery and analysis tool, built with Plotly Dash.

## Features

### 🎯 Core Features
- **Interactive Job Management**: View, filter, and manage scraped jobs
- **Real-time Analytics**: Live charts and metrics for job market insights
- **Profile Integration**: Seamless integration with JobQst user profiles
- **Advanced Filtering**: Search, filter by company, status, date range, and match score
- **Export Capabilities**: Export filtered results to CSV, Excel, or JSON

### 📊 Analytics & Visualizations
- Match score distribution histograms
- Job timeline and trends analysis
- Status distribution pie charts
- Top companies and locations analysis
- Application funnel visualization
- Salary distribution analysis
- Skills demand tracking

### ⚙️ Processing Controls
- Start/stop/pause job scraping
- Real-time progress monitoring
- Processing queue management
- Batch job operations

### 🔧 System Monitoring
- Health status indicators
- Resource usage monitoring
- Error logs and alerts
- Performance metrics

## Quick Start

### Prerequisites
- Python 3.8 or higher
- JobQst project environment
- Active conda environment: `auto_job`

### Installation & Setup

1. **Navigate to the dashboard directory:**
   ```bash
   cd src/dashboard/dash_app
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```
   
   The setup script will:
   - Check Python version compatibility
   - Install required dependencies
   - Create necessary directories
   - Setup environment variables
   - Test database connection
   - Start the dashboard

3. **Manual setup (alternative):**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the dashboard
   python app.py
   ```

4. **Access the dashboard:**
   Open your browser and go to: `http://127.0.0.1:8050`

## Usage

### Navigation
The dashboard features a sidebar navigation with the following sections:

- **📋 Jobs**: Main job listing and management interface
- **📊 Analytics**: Charts and insights about your job search
- **⚙️ Processing**: Control job scraping and processing
- **🔧 System**: Monitor system health and performance
- **⚙️ Settings**: Configure dashboard preferences

### Job Management
1. **View Jobs**: Browse all scraped jobs in an interactive table
2. **Filter & Search**: Use the search bar and filters to find specific jobs
3. **Job Actions**: View job details, apply, or add notes
4. **Export Data**: Export filtered results for external analysis

### Analytics
- **KPI Cards**: Quick overview of key metrics
- **Interactive Charts**: Hover and click for detailed information
- **Time-based Analysis**: Track trends over time
- **Comparative Insights**: Compare companies, locations, and skills

### Processing Controls
- **Start Processing**: Begin new job scraping sessions
- **Monitor Progress**: Real-time updates on scraping progress
- **Queue Management**: View and manage processing queues
- **Batch Operations**: Perform bulk actions on multiple jobs

## Configuration

### Environment Variables
```bash
DASH_DEBUG=True          # Enable debug mode
DASH_HOST=127.0.0.1      # Host to bind to
DASH_PORT=8050           # Port to run on
DASH_LOG_LEVEL=INFO      # Logging level
```

### Configuration File
The dashboard uses `config/dashboard_config.json` for detailed configuration:

```json
{
  "app": {
    "title": "JobQst Dashboard",
    "theme": "bootstrap",
    "debug": true,
    "host": "127.0.0.1",
    "port": 8050
  },
  "data": {
    "refresh_interval": 30000,
    "max_jobs_display": 1000,
    "cache_timeout": 300
  },
  "ui": {
    "items_per_page": 25,
    "chart_height": 400,
    "date_format": "%Y-%m-%d"
  },
  "features": {
    "auto_save": true,
    "real_time_updates": true,
    "export_enabled": true,
    "analytics_enabled": true
  }
}
```

## Architecture

### Project Structure
```
dash_app/
├── app.py                 # Main application entry point
├── config.py             # App configuration and setup
├── setup.py              # Installation and setup script
├── requirements.txt      # Python dependencies
│
├── layouts/              # Page layouts
│   ├── __init__.py
│   ├── jobs.py          # Jobs page layout
│   ├── analytics.py     # Analytics page layout
│   ├── processing.py    # Processing page layout
│   ├── system.py        # System monitoring layout
│   └── settings.py      # Settings page layout
│
├── callbacks/            # Interactive callbacks
│   ├── __init__.py
│   ├── jobs_callbacks.py
│   ├── analytics_callbacks.py
│   ├── processing_callbacks.py
│   ├── system_callbacks.py
│   └── settings_callbacks.py
│
├── components/           # Reusable UI components
│   ├── __init__.py
│   ├── sidebar.py       # Navigation sidebar
│   └── common.py        # Common UI elements
│
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── data_loader.py   # Data loading and caching
│   ├── formatters.py    # Data formatting utilities
│   ├── charts.py        # Chart generation functions
│   └── config_manager.py # Configuration management
│
├── assets/              # Static assets
│   ├── style.css        # Custom CSS styling
│   └── exports/         # Export file storage
│
└── config/              # Configuration files
    └── dashboard_config.json
```

### Key Components

1. **App.py**: Main Dash application with routing and layout
2. **Layouts**: Modular page layouts for different sections
3. **Callbacks**: Interactive functions handling user inputs
4. **Components**: Reusable UI components (sidebar, tables, etc.)
5. **Utils**: Data loading, formatting, and chart generation
6. **Assets**: CSS styling and static files

## Integration with JobQst

The dashboard integrates seamlessly with the JobQst ecosystem:

- **Profile Manager**: Loads user profiles and preferences
- **Job Database**: Connects to the SQLite/PostgreSQL job database
- **Scraping Service**: Interfaces with job scraping components
- **Analysis Pipeline**: Displays results from job analysis

## Development

### Adding New Features

1. **New Page**: Add layout in `layouts/` and callbacks in `callbacks/`
2. **New Chart**: Add chart function in `utils/charts.py`
3. **New Component**: Create in `components/` and import in layouts
4. **Configuration**: Add settings to `config/dashboard_config.json`

### Debugging

1. **Enable Debug Mode**: Set `DASH_DEBUG=True`
2. **Check Logs**: Monitor console output for errors
3. **Inspect Elements**: Use browser developer tools
4. **Callback Graph**: Use Dash's built-in callback debugging

### Testing

```bash
# Run with test data
python app.py --test-mode

# Check configuration
python -c "from utils.config_manager import get_config; print(get_config().validate())"
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Change port in config or environment
   export DASH_PORT=8051
   python app.py
   ```

2. **Import Errors**:
   ```bash
   # Ensure you're in the auto_job environment
   conda activate auto_job
   pip install -r requirements.txt
   ```

3. **Database Connection Issues**:
   - Check if JobQst is properly configured
   - Verify profile exists and database is accessible
   - Review connection settings in config

4. **Missing Data**:
   - Run job scraping first: `python main.py <profile> --action scrape`
   - Check if profile has any job data
   - Verify database permissions

### Performance Optimization

1. **Large Datasets**: Enable pagination and virtual scrolling
2. **Slow Charts**: Reduce data points or use sampling
3. **Memory Usage**: Clear cache and enable compression
4. **Network Issues**: Adjust refresh intervals

## Contributing

1. Follow the existing code structure and naming conventions
2. Add proper error handling and logging
3. Update documentation for new features
4. Test with different profiles and data sizes
5. Ensure mobile responsiveness

## License

This dashboard is part of the JobQst project. See the main project LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the main JobQst documentation
3. Check logs for detailed error messages
4. Ensure proper environment setup

---

**Note**: This dashboard requires an active JobQst installation and user profile to function properly. Make sure to run job scraping operations first to populate the dashboard with data.