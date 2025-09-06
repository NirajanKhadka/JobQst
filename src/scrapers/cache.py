import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set, Dict


class ScrapingCache:
    def __init__(self, profile_name: str, cache_duration_hours: int = 6):
        self.profile_name = profile_name
        self.cache_dir = Path("output") / "scraping_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.processed_urls: Set[str] = set()
        self.keyword_performance: Dict[str, Dict] = {}
        self._load_cache()

    def _load_cache(self):
        cache_file = self.cache_dir / f"{self.profile_name}_cache.json"
        if not cache_file.exists():
            return

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
        if datetime.now() - cache_time < self.cache_duration:
            self.processed_urls = set(cache_data.get("processed_urls", []))
            self.keyword_performance = cache_data.get("keyword_performance", {})

    def save_cache(self, metrics: Dict):
        cache_file = self.cache_dir / f"{self.profile_name}_cache.json"
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "processed_urls": list(self.processed_urls),
            "keyword_performance": self.keyword_performance,
            "metrics": metrics,
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

    def is_url_processed(self, url: str) -> bool:
        return url in self.processed_urls

    def add_processed_url(self, url: str):
        self.processed_urls.add(url)

