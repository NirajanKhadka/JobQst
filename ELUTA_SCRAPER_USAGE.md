# Eluta Scraper Usage Guide

This document explains how to run the eluta scraper with the specific options "1 and 1 from cli" as requested.

## Understanding the Options

When you refer to "option 1 and 1 from cli", you're referring to the following selections in the interactive CLI:

1. **Main Menu Option 1**: "Job Scraping (NEW Fast 3-Phase Pipeline - 4.6x faster)"
2. **Site Selection Option 1**: "Eluta.ca (NEW Fast Pipeline - Recommended)"
3. **Pipeline Mode Option 1**: "Fast Pipeline - Standard (4 workers, reliable)"

## Direct Command Line Usage

Instead of using the interactive CLI, you can directly run the eluta scraper with these options using the following command:

```bash
python main.py [profile_name] --action scrape
```

This command will:
- Use the Fast 3-Phase Pipeline (4.6x faster than the old system)
- Automatically select Eluta as the job site
- Use the Standard pipeline mode with 4 workers

## Additional Options

You can customize the scraping behavior with additional parameters:

```bash
python main.py [profile_name] --action scrape --pages 3 --jobs 20 --headless
```

Available options include:
- `--pages`: Number of pages to scrape per keyword (default: 3)
- `--jobs`: Number of jobs to collect per keyword (default: 20)
- `--headless`: Run browser in headless mode (no visible browser window)
- `--days`: Number of days to look back (7, 14, or 30)

## Interactive Mode

If you prefer to use the interactive menu, run:

```bash
python main.py [profile_name]
```

Then follow these steps:
1. Select option 1: "Job Scraping (NEW Fast 3-Phase Pipeline - 4.6x faster)"
2. Select option 1: "Eluta.ca (NEW Fast Pipeline - Recommended)"
3. Select option 1: "Fast Pipeline - Standard (4 workers, reliable)"

## Performance Information

The Fast 3-Phase Pipeline provides significant performance improvements:
- **Phase 1**: Eluta URLs collection
- **Phase 2**: Parallel external job scraping
- **Phase 3**: GPU-accelerated job processing

This approach is 4.6x faster than the previous system.