from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Get Redis URL from environment or use default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'botsmith',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.tasks']  # Import tasks module
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    'backend.tasks.process_document': {'queue': 'documents'},
    'backend.tasks.scrape_website': {'queue': 'websites'},
    'backend.tasks.send_notification': {'queue': 'notifications'},
    'backend.tasks.*': {'queue': 'default'},
}

if __name__ == '__main__':
    celery_app.start()
