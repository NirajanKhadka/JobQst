import sys

dependencies = [
    'redis',
    'fastapi', 
    'uvicorn',
    'psutil',
    'asyncio'
]

print("Dependency Check Results:")
print("=" * 40)

for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep}: Available")
    except ImportError as e:
        print(f"❌ {dep}: Missing - {e}")

print("\nJobStatus enum check:")
try:
    from src.scrapers.scraping_models import JobStatus
    print(f"✅ JobStatus from scraping_models: {list(JobStatus)}")
except Exception as e:
    print(f"❌ JobStatus from scraping_models: {e}")

try:
    from src.orchestration.job_queue_manager import JobStatus as QueueJobStatus
    print(f"✅ JobStatus from job_queue_manager: {list(QueueJobStatus)}")
except Exception as e:
    print(f"❌ JobStatus from job_queue_manager: {e}")