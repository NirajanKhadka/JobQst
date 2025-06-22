"""
Multi-Site Job Scraper
Combines results from multiple job site scrapers.
"""

import random
import time
from typing import Dict, Generator, List
from rich.console import Console

console = Console()


class MultiSiteScraper:
    """
    Combines multiple site-specific scrapers to provide unified job scraping.
    """
    
    def __init__(self, scrapers: Dict, profile: Dict):
        """
        Initialize with a dictionary of scrapers.
        
        Args:
            scrapers: Dictionary mapping site names to scraper instances
            profile: User profile dictionary
        """
        self.scrapers = scrapers
        self.profile = profile
        self.current_site_index = 0
        self.site_names = list(scrapers.keys())
        
        console.print(f"[green]Initialized multi-site scraper with: {', '.join(self.site_names)}[/green]")
    
    def batched(self, batch_size: int, round_robin: bool = True) -> Generator[List[Dict], None, None]:
        """
        Generate batches of jobs from multiple sites.
        
        Args:
            batch_size: Number of jobs to include in each batch
            round_robin: If True, alternate between sites; if False, exhaust each site
            
        Yields:
            List of job dictionaries in each batch
        """
        if round_robin:
            yield from self._batched_round_robin(batch_size)
        else:
            yield from self._batched_sequential(batch_size)
    
    def _batched_round_robin(self, batch_size: int) -> Generator[List[Dict], None, None]:
        """
        Generate batches using round-robin approach across sites.
        """
        batch = []
        site_generators = {}
        
        # Initialize generators for each site
        for site_name, scraper in self.scrapers.items():
            try:
                site_generators[site_name] = scraper.scrape_jobs()
                console.print(f"[green]Initialized {site_name} scraper[/green]")
            except Exception as e:
                console.print(f"[red]Failed to initialize {site_name} scraper: {e}[/red]")
        
        # Round-robin through sites
        while site_generators:
            sites_to_remove = []
            
            for site_name in list(site_generators.keys()):
                try:
                    # Try to get one job from this site
                    job = next(site_generators[site_name])
                    batch.append(job)
                    
                    console.print(f"[cyan]Got job from {site_name}: {job.get('title', 'Unknown')}[/cyan]")
                    
                    # If batch is full, yield it
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        
                        # Add delay between batches
                        delay = random.uniform(2.0, 4.0)
                        time.sleep(delay)
                    
                except StopIteration:
                    # This site is exhausted
                    console.print(f"[yellow]{site_name} scraper exhausted[/yellow]")
                    sites_to_remove.append(site_name)
                except Exception as e:
                    console.print(f"[red]Error from {site_name} scraper: {e}[/red]")
                    sites_to_remove.append(site_name)
            
            # Remove exhausted sites
            for site_name in sites_to_remove:
                del site_generators[site_name]
            
            # If no more sites, break
            if not site_generators:
                break
        
        # Yield remaining jobs
        if batch:
            yield batch
    
    def _batched_sequential(self, batch_size: int) -> Generator[List[Dict], None, None]:
        """
        Generate batches by exhausting each site sequentially.
        """
        for site_name, scraper in self.scrapers.items():
            console.print(f"[cyan]Starting sequential scraping from {site_name}[/cyan]")
            
            try:
                for batch in scraper.batched(batch_size):
                    yield batch
                    
                    # Add delay between batches
                    delay = random.uniform(2.0, 4.0)
                    time.sleep(delay)
                    
            except Exception as e:
                console.print(f"[red]Error scraping {site_name}: {e}[/red]")
                continue
    
    def scrape_all_sites(self, max_jobs_per_site: int = 50) -> List[Dict]:
        """
        Scrape a limited number of jobs from all sites.
        
        Args:
            max_jobs_per_site: Maximum number of jobs to scrape from each site
            
        Returns:
            List of all scraped jobs
        """
        all_jobs = []
        
        for site_name, scraper in self.scrapers.items():
            console.print(f"[cyan]Scraping up to {max_jobs_per_site} jobs from {site_name}[/cyan]")
            
            try:
                site_jobs = []
                for job in scraper.scrape_jobs():
                    site_jobs.append(job)
                    
                    if len(site_jobs) >= max_jobs_per_site:
                        break
                
                all_jobs.extend(site_jobs)
                console.print(f"[green]Scraped {len(site_jobs)} jobs from {site_name}[/green]")
                
                # Add delay between sites
                if site_name != list(self.scrapers.keys())[-1]:  # Not the last site
                    delay = random.uniform(3.0, 6.0)
                    time.sleep(delay)
                    
            except Exception as e:
                console.print(f"[red]Error scraping {site_name}: {e}[/red]")
                continue
        
        console.print(f"[bold green]Total jobs scraped: {len(all_jobs)}[/bold green]")
        return all_jobs
    
    def get_site_statistics(self) -> Dict[str, Dict]:
        """
        Get statistics about available scrapers.
        
        Returns:
            Dictionary with statistics for each site
        """
        stats = {}
        
        for site_name, scraper in self.scrapers.items():
            stats[site_name] = {
                "site_name": scraper.site_name,
                "base_url": scraper.base_url,
                "requires_browser": scraper.requires_browser,
                "rate_limit_delay": scraper.rate_limit_delay,
                "search_terms": scraper.search_terms,
                "location": scraper.location,
            }
        
        return stats
    
    def test_all_scrapers(self, max_jobs: int = 3) -> Dict[str, List[Dict]]:
        """
        Test all scrapers by getting a few jobs from each.
        
        Args:
            max_jobs: Maximum number of jobs to test from each scraper
            
        Returns:
            Dictionary mapping site names to lists of test jobs
        """
        test_results = {}
        
        for site_name, scraper in self.scrapers.items():
            console.print(f"[cyan]Testing {site_name} scraper...[/cyan]")
            
            try:
                jobs = []
                for job in scraper.scrape_jobs():
                    jobs.append(job)
                    
                    if len(jobs) >= max_jobs:
                        break
                
                test_results[site_name] = jobs
                console.print(f"[green]{site_name}: {len(jobs)} jobs scraped successfully[/green]")
                
            except Exception as e:
                console.print(f"[red]{site_name}: Error - {e}[/red]")
                test_results[site_name] = []
        
        return test_results
    
    def add_scraper(self, site_name: str, scraper) -> None:
        """
        Add a new scraper to the multi-site scraper.
        
        Args:
            site_name: Name of the site
            scraper: Scraper instance
        """
        self.scrapers[site_name] = scraper
        self.site_names = list(self.scrapers.keys())
        console.print(f"[green]Added {site_name} scraper[/green]")
    
    def remove_scraper(self, site_name: str) -> None:
        """
        Remove a scraper from the multi-site scraper.
        
        Args:
            site_name: Name of the site to remove
        """
        if site_name in self.scrapers:
            del self.scrapers[site_name]
            self.site_names = list(self.scrapers.keys())
            console.print(f"[yellow]Removed {site_name} scraper[/yellow]")
        else:
            console.print(f"[red]Scraper {site_name} not found[/red]")
    
    def get_jobs_by_site(self, site_name: str, count: int = 10) -> List[Dict]:
        """
        Get jobs from a specific site.
        
        Args:
            site_name: Name of the site
            count: Number of jobs to retrieve
            
        Returns:
            List of jobs from the specified site
        """
        if site_name not in self.scrapers:
            console.print(f"[red]Scraper {site_name} not found[/red]")
            return []
        
        scraper = self.scrapers[site_name]
        jobs = []
        
        try:
            for job in scraper.scrape_jobs():
                jobs.append(job)
                
                if len(jobs) >= count:
                    break
            
            console.print(f"[green]Retrieved {len(jobs)} jobs from {site_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error getting jobs from {site_name}: {e}[/red]")
        
        return jobs
