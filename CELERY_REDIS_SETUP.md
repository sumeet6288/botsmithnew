# 🎉 Celery + Redis Background Task Processing - Complete Setup

## ✅ Installation Complete (December 15, 2025)

### What Was Added

Successfully integrated **Celery 5.6.0** and **Redis 7.0.15** for robust background task processing in the BotSmith AI Chatbot Builder application.

---

## 🚀 Components Installed

### 1. Redis Server
- **Version**: 7.0.15
- **Port**: 6379 (localhost)
- **Status**: ✅ Running
- **Configuration**: Optimized for task queue performance

### 2. Celery Worker
- **Version**: 5.6.0
- **Concurrency**: 4 workers
- **Status**: ✅ Running
- **Task Queues**: default, documents, websites, notifications

### 3. Celery Beat
- **Status**: ✅ Running
- **Purpose**: Periodic task scheduler for automated jobs

---

## 📁 Files Created

### Backend Files

1. **`/app/backend/celery_app.py`**
   - Main Celery application configuration
   - Redis broker and result backend setup
   - Task routing configuration
   - Worker settings (prefetch, time limits, etc.)

2. **`/app/backend/tasks.py`**
   - Background task definitions:
     - `process_document` - Process uploaded files
     - `scrape_website` - Scrape website content
     - `send_notification` - Send notifications to users
     - `cleanup_old_data` - Clean up old conversations/messages
     - `generate_analytics_report` - Generate analytics reports

### Configuration Files

3. **`/etc/supervisor/conf.d/celery.conf`**
   - Supervisor configuration for Celery worker and beat
   - Auto-restart and logging settings

4. **`/etc/supervisor/conf.d/redis.conf`**
   - Supervisor configuration for Redis server

### Environment Configuration

5. **`/app/backend/.env`** (Updated)
   - Added Redis configuration:
     ```
     REDIS_URL="redis://localhost:6379/0"
     CELERY_BROKER_URL="redis://localhost:6379/0"
     CELERY_RESULT_BACKEND="redis://localhost:6379/0"
     ```

6. **`/app/backend/requirements.txt`** (Updated)
   - Added dependencies:
     ```
     redis==7.1.0
     celery==5.6.0
     ```

---

## 🎯 Background Tasks Available

### 1. Document Processing Task
```python
from backend.tasks import process_document

# Queue a document processing task
result = process_document.delay(
    source_id='source_123',
    file_path='/path/to/file.pdf',
    chatbot_id='chatbot_456'
)
```

**What it does:**
- Processes uploaded documents (PDF, DOCX, TXT, XLSX, CSV)
- Extracts text content
- Chunks content for RAG system
- Stores chunks in MongoDB
- Updates source status

### 2. Website Scraping Task
```python
from backend.tasks import scrape_website

# Queue a website scraping task
result = scrape_website.delay(
    source_id='source_123',
    url='https://example.com',
    chatbot_id='chatbot_456'
)
```

**What it does:**
- Scrapes website content
- Extracts text and metadata
- Chunks content
- Stores in MongoDB

### 3. Notification Task
```python
from backend.tasks import send_notification

# Send notification to user
result = send_notification.delay(
    user_id='user_123',
    title='Document Processed',
    message='Your document has been successfully processed',
    notification_type='info'
)
```

### 4. Data Cleanup Task
```python
from backend.tasks import cleanup_old_data

# Clean up data older than 90 days
result = cleanup_old_data.delay(days=90)
```

### 5. Analytics Report Generation
```python
from backend.tasks import generate_analytics_report

# Generate 30-day analytics report
result = generate_analytics_report.delay(
    chatbot_id='chatbot_456',
    period='30d'
)
```

---

## 🔧 How to Use in Your Code

### In FastAPI Endpoints

```python
from fastapi import APIRouter, UploadFile
from backend.tasks import process_document

router = APIRouter()

@router.post("/upload-document")
async def upload_document(file: UploadFile, chatbot_id: str):
    # Save file to disk
    file_path = f"/app/backend/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Create source record in database
    source_id = create_source_record(chatbot_id, file.filename)
    
    # Queue background task (non-blocking)
    task = process_document.delay(
        source_id=source_id,
        file_path=file_path,
        chatbot_id=chatbot_id
    )
    
    return {
        "message": "File uploaded successfully",
        "source_id": source_id,
        "task_id": task.id,
        "status": "processing"
    }
```

### Checking Task Status

```python
from celery.result import AsyncResult

@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    task = AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.state,  # PENDING, STARTED, SUCCESS, FAILURE
        "result": task.result if task.ready() else None,
        "error": str(task.info) if task.failed() else None
    }
```

---

## 🎮 Management Commands

### Check Celery Worker Status
```bash
celery -A backend.celery_app inspect active
celery -A backend.celery_app inspect stats
```

### Monitor Tasks
```bash
celery -A backend.celery_app events
```

### Purge All Tasks
```bash
celery -A backend.celery_app purge
```

### Control Workers
```bash
# Restart workers
sudo supervisorctl restart celery-worker celery-beat

# Stop workers
sudo supervisorctl stop celery-worker celery-beat

# Check status
sudo supervisorctl status
```

---

## 📊 Monitoring

### Redis Monitoring
```bash
# Check Redis status
redis-cli ping

# Monitor Redis in real-time
redis-cli monitor

# Check Redis stats
redis-cli info stats

# View all keys
redis-cli keys '*'
```

### View Logs
```bash
# Celery worker logs
tail -f /var/log/supervisor/celery-worker.out.log
tail -f /var/log/supervisor/celery-worker.err.log

# Celery beat logs
tail -f /var/log/supervisor/celery-beat.out.log
tail -f /var/log/supervisor/celery-beat.err.log

# Redis logs
tail -f /var/log/supervisor/redis.out.log
```

---

## ⚙️ Configuration Details

### Celery Settings
- **Broker**: Redis (localhost:6379/0)
- **Result Backend**: Redis (localhost:6379/0)
- **Task Serializer**: JSON
- **Result Serializer**: JSON
- **Timezone**: UTC
- **Task Time Limit**: 30 minutes
- **Soft Time Limit**: 25 minutes
- **Worker Prefetch Multiplier**: 4
- **Max Tasks Per Child**: 1000

### Task Queues
- **default**: General tasks
- **documents**: Document processing
- **websites**: Website scraping
- **notifications**: Notification sending

---

## 🚨 Troubleshooting

### Celery Worker Not Starting
```bash
# Check logs
tail -100 /var/log/supervisor/celery-worker.err.log

# Restart worker
sudo supervisorctl restart celery-worker
```

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Check Redis connections
redis-cli client list

# Restart Redis
pkill redis-server
/usr/bin/redis-server --port 6379 --bind 127.0.0.1 --daemonize yes
```

### Task Stuck or Not Executing
```bash
# Check active tasks
celery -A backend.celery_app inspect active

# Purge all pending tasks
celery -A backend.celery_app purge

# Restart workers
sudo supervisorctl restart celery-worker celery-beat
```

---

## 📈 Benefits of This Setup

### 1. Non-Blocking Operations
- API endpoints return immediately
- Long-running tasks execute in background
- Better user experience

### 2. Scalability
- Add more workers for increased throughput
- Distribute tasks across multiple machines
- Queue-based architecture handles load spikes

### 3. Reliability
- Task retries on failure
- Supervisor auto-restarts workers
- Redis persistence (optional)

### 4. Monitoring
- Built-in task status tracking
- Celery events for real-time monitoring
- Redis statistics

### 5. Flexibility
- Easy to add new task types
- Configure task priorities
- Schedule periodic tasks with Celery Beat

---

## 🎯 Next Steps

### 1. Add More Tasks
Create additional background tasks for:
- Email sending
- Report generation
- Data exports
- Batch operations
- Model training

### 2. Implement Task Scheduling
Use Celery Beat to schedule periodic tasks:
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-daily': {
        'task': 'backend.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': (90,)  # 90 days
    },
}
```

### 3. Add Monitoring Dashboard
Consider installing:
- **Flower**: Web-based Celery monitoring tool
  ```bash
  pip install flower
  celery -A backend.celery_app flower
  ```

### 4. Implement Task Callbacks
Add callbacks for task completion:
```python
@celery_app.task
def on_document_processed(result):
    # Send notification to user
    send_notification.delay(
        user_id=result['user_id'],
        title='Document Ready',
        message='Your document has been processed'
    )
```

---

## ✅ Verification

### Services Running
- ✅ Backend (FastAPI) - Port 8001
- ✅ Frontend (React) - Port 3000
- ✅ MongoDB - Port 27017
- ✅ Redis - Port 6379
- ✅ Celery Worker - 4 concurrent workers
- ✅ Celery Beat - Periodic scheduler

### Test Task Execution
```python
# In Python shell
from backend.tasks import send_notification

# Queue a test task
result = send_notification.delay(
    user_id='test_user',
    title='Test Notification',
    message='Celery is working!',
    notification_type='info'
)

print(f"Task ID: {result.id}")
print(f"Status: {result.state}")

# Wait for result
print(f"Result: {result.get(timeout=10)}")
```

---

## 📞 Support

For issues or questions:
1. Check logs in `/var/log/supervisor/`
2. Verify Redis is running: `redis-cli ping`
3. Check Celery worker status: `supervisorctl status`
4. Review task code in `/app/backend/tasks.py`

---

## 🎉 Success!

Your application now has a powerful background task processing system!
- Queue long-running operations
- Improve API response times
- Scale horizontally as needed
- Monitor tasks in real-time

Happy coding! 🚀
