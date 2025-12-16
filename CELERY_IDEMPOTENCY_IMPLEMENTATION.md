# 🎯 Celery Task Idempotency Implementation

## ✅ Complete Implementation (December 2025)

### Overview
Implemented comprehensive task idempotency for all Celery background tasks to prevent duplicate execution and ensure reliable task processing even during retries, network failures, or system crashes.

---

## 🔑 Key Features Implemented

### 1. **Task Deduplication**
- ✅ Unique task ID generation based on task name and parameters
- ✅ SHA-256 hashing of task arguments for consistent IDs
- ✅ Redis-based distributed locking mechanism
- ✅ Prevents multiple workers from executing the same task

### 2. **Result Caching**
- ✅ Successful task results cached in Redis for 1 hour
- ✅ Duplicate tasks return cached results immediately
- ✅ Configurable TTL (Time To Live) per task type
- ✅ Automatic cache cleanup

### 3. **Retry Logic with Exponential Backoff**
- ✅ Automatic retry on task failure (up to 3 attempts)
- ✅ Exponential backoff: 1min, 2min, 4min
- ✅ Different retry strategies per task type
- ✅ Graceful handling of max retries exceeded

### 4. **Reliability Configurations**
- ✅ Late acknowledgment (task_acks_late=True)
- ✅ Task rejection on worker crash
- ✅ Result persistence for deduplication
- ✅ Prefetch multiplier set to 1 for reliability

---

## 🏗️ Architecture

### IdempotentTask Base Class

```python
class IdempotentTask(Task):
    """Base task class with built-in idempotency"""
    
    # 1. Generate unique task ID from arguments
    def generate_task_id(self, *args, **kwargs)
    
    # 2. Acquire distributed lock
    def acquire_lock(self, task_id: str, timeout: int = 3600)
    
    # 3. Check cached results
    def get_cached_result(self, task_id: str)
    
    # 4. Cache successful results
    def cache_result(self, task_id: str, result: Dict)
    
    # 5. Release lock after execution
    def release_lock(self, task_id: str)
```

### Execution Flow

```
1. Task submitted → Generate unique task ID
                    ↓
2. Check cached result → Found? → Return cached result ✅
                    ↓ Not found
3. Try acquire lock → Lock held? → Wait/Skip duplicate ⚠️
                    ↓ Lock acquired
4. Execute task logic
                    ↓
5. Cache result (if successful)
                    ↓
6. Release lock
                    ↓
7. Return result ✅
```

---

## 📋 Tasks with Idempotency

### 1. process_document
**Configuration:**
- Max retries: 3
- Retry delay: 60 seconds (exponential backoff)
- Result cache: 1 hour
- Queue: documents

**Idempotency Guarantee:**
- Same document won't be processed multiple times
- If task fails and retries, chunks won't be duplicated
- If document already processed, returns cached result

**Usage:**
```python
from backend.tasks import process_document

# First call - processes document
result1 = process_document.delay('source_123', '/path/file.pdf', 'chatbot_456')

# Second call with same params - returns cached result
result2 = process_document.delay('source_123', '/path/file.pdf', 'chatbot_456')
```

### 2. scrape_website
**Configuration:**
- Max retries: 3
- Retry delay: 60 seconds (exponential backoff)
- Result cache: 1 hour
- Queue: websites

**Idempotency Guarantee:**
- Same URL won't be scraped multiple times concurrently
- Network failures trigger retry with backoff
- Prevents duplicate content chunks in database

**Usage:**
```python
from backend.tasks import scrape_website

# Scrape website (idempotent)
result = scrape_website.delay('source_789', 'https://example.com', 'chatbot_456')
```

### 3. send_notification
**Configuration:**
- Max retries: 3
- Retry delay: 30 seconds (exponential backoff)
- Result cache: 1 hour
- Queue: notifications

**Idempotency Guarantee:**
- Same notification won't be sent multiple times
- Prevents duplicate notifications in user's inbox
- Fast retry for critical notifications

**Usage:**
```python
from backend.tasks import send_notification

# Send notification (won't duplicate)
result = send_notification.delay(
    'user_123',
    'Document Ready',
    'Your document has been processed',
    'info'
)
```

### 4. cleanup_old_data
**Configuration:**
- Max retries: 2
- Result cache: 1 hour
- Queue: default

**Idempotency Guarantee:**
- Multiple cleanup calls won't delete data multiple times
- Safe to run multiple times with same parameters

**Usage:**
```python
from backend.tasks import cleanup_old_data

# Cleanup data older than 90 days
result = cleanup_old_data.delay(days=90)
```

### 5. generate_analytics_report
**Configuration:**
- Max retries: 2
- Result cache: 1 hour
- Queue: default

**Idempotency Guarantee:**
- Same report won't be generated multiple times
- Cached results returned for duplicate requests
- Resource-efficient for expensive computations

**Usage:**
```python
from backend.tasks import generate_analytics_report

# Generate report (cached for 1 hour)
result = generate_analytics_report.delay('chatbot_456', '30d')
```

---

## 🔧 Configuration Changes

### celery_app.py Updates

```python
celery_app.conf.update(
    # Idempotency configurations
    task_acks_late=True,              # Acknowledge after completion
    worker_prefetch_multiplier=1,     # One task at a time
    task_reject_on_worker_lost=True,  # Reject if worker crashes
    task_ignore_result=False,         # Store results for checks
    result_expires=3600,              # Keep results 1 hour
    task_default_retry_delay=60,      # 1 minute default retry
    task_max_retries=3,               # Max 3 retries
)
```

### tasks.py Updates

1. **Added IdempotentTask base class** with:
   - Unique task ID generation (SHA-256)
   - Redis distributed locking
   - Result caching mechanism
   - Lock acquisition/release

2. **Updated all task decorators**:
   ```python
   @celery_app.task(
       name='backend.tasks.process_document',
       bind=True,
       base=IdempotentTask,  # ← New
       max_retries=3,        # ← New
       default_retry_delay=60 # ← New
   )
   ```

3. **Added retry logic** with exponential backoff:
   ```python
   try:
       raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
   except self.MaxRetriesExceededError:
       return {'status': 'failed', 'error': str(e)}
   ```

---

## 🧪 Testing Idempotency

### Test 1: Duplicate Task Prevention
```python
import time
from backend.tasks import process_document

# Submit same task twice
task1 = process_document.delay('doc_123', '/path/file.pdf', 'bot_456')
task2 = process_document.delay('doc_123', '/path/file.pdf', 'bot_456')

# task2 should skip or return cached result
print(task2.get())  # {'status': 'skipped', 'reason': 'duplicate_task'}
```

### Test 2: Result Caching
```python
from backend.tasks import generate_analytics_report

# First call - computes report
result1 = generate_analytics_report.delay('bot_456', '30d')
print(result1.get())  # Executes and caches

# Second call within 1 hour - returns cached
result2 = generate_analytics_report.delay('bot_456', '30d')
print(result2.get())  # Instant cached result
```

### Test 3: Retry with Exponential Backoff
```python
from backend.tasks import scrape_website

# Submit task that will fail
task = scrape_website.delay('src_123', 'http://invalid-url', 'bot_456')

# Monitor retries
# Retry 1: 60 seconds wait
# Retry 2: 120 seconds wait (2^1 * 60)
# Retry 3: 240 seconds wait (2^2 * 60)
```

### Test 4: Concurrent Execution Prevention
```python
import concurrent.futures
from backend.tasks import process_document

# Submit same task from multiple threads
def submit_task():
    return process_document.delay('doc_999', '/path/file.pdf', 'bot_456')

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(submit_task) for _ in range(10)]
    results = [f.result().get() for f in futures]

# Only 1 task executes, others skip or wait
print(results)
```

---

## 📊 Monitoring Idempotency

### Check Redis Locks
```bash
# View active task locks
redis-cli keys "task_lock:*"

# Check specific task lock
redis-cli get "task_lock:backend.tasks.process_document:abc123..."
```

### Check Cached Results
```bash
# View cached results
redis-cli keys "task_result:*"

# Get specific cached result
redis-cli get "task_result:backend.tasks.process_document:abc123..."
```

### Monitor Task Status
```python
from celery.result import AsyncResult

task_id = 'your-task-id'
result = AsyncResult(task_id)

print(f"Status: {result.state}")
print(f"Result: {result.result}")
print(f"Traceback: {result.traceback}")
```

### Celery Inspect Commands
```bash
# Check active tasks
celery -A backend.celery_app inspect active

# Check registered tasks
celery -A backend.celery_app inspect registered

# Check task stats
celery -A backend.celery_app inspect stats
```

---

## ⚙️ Configuration Options

### Per-Task Configuration

You can customize idempotency per task:

```python
@celery_app.task(
    name='custom_task',
    bind=True,
    base=IdempotentTask,
    max_retries=5,           # More retries
    default_retry_delay=30,  # Shorter delay
)
def custom_task(self, param1, param2):
    # Custom result cache TTL
    result = {'status': 'success', 'data': 'value'}
    self.cache_result(
        self.generate_task_id(param1, param2),
        result,
        ttl=7200  # Cache for 2 hours
    )
    return result
```

### Global Configuration

Adjust in `celery_app.py`:

```python
celery_app.conf.update(
    result_expires=7200,          # Change cache duration
    task_default_retry_delay=120, # Change default retry delay
    task_max_retries=5,           # Change max retries
)
```

---

## 🚨 Error Handling

### Task Failure Scenarios

1. **Temporary Failure (Network Issue)**
   - Task retries with exponential backoff
   - Lock released after each attempt
   - New lock acquired for retry

2. **Permanent Failure (Invalid Data)**
   - Max retries exhausted
   - Error logged and returned
   - Lock released
   - No result cached (prevents bad data)

3. **Worker Crash**
   - Task rejected (task_reject_on_worker_lost=True)
   - Lock expires automatically (1 hour timeout)
   - Task requeued by Celery
   - New worker picks up task

4. **Duplicate Submission**
   - Lock check detects duplicate
   - Waits for original task or returns cached result
   - No duplicate execution

---

## 📈 Benefits

### 1. Data Integrity
- ✅ No duplicate document processing
- ✅ No duplicate notifications
- ✅ No duplicate database entries
- ✅ Consistent results across retries

### 2. Resource Efficiency
- ✅ Cached results save computation
- ✅ No wasted processing on duplicates
- ✅ Better worker utilization
- ✅ Reduced database load

### 3. Reliability
- ✅ Automatic retry on failure
- ✅ Exponential backoff prevents system overload
- ✅ Handles worker crashes gracefully
- ✅ Distributed locking prevents race conditions

### 4. Scalability
- ✅ Works with multiple workers
- ✅ Redis-based locking scales horizontally
- ✅ Result caching reduces load
- ✅ Queue-based architecture

---

## 🔍 Best Practices

### 1. Task Design
- Keep tasks idempotent by design
- Use unique identifiers (source_id, chatbot_id)
- Check database state before modifications
- Use upsert operations where possible

### 2. Retry Strategy
- Use exponential backoff for external APIs
- Set appropriate max retries based on task type
- Critical tasks: more retries (5+)
- Background tasks: fewer retries (2-3)

### 3. Result Caching
- Cache expensive computations (analytics)
- Short TTL for time-sensitive data (5-15 min)
- Long TTL for static data (1+ hour)
- Clear cache on data updates

### 4. Monitoring
- Monitor Redis memory usage
- Track task success/failure rates
- Alert on high retry rates
- Monitor lock acquisition failures

---

## 🎯 Use Cases

### When Idempotency Helps

1. **Document Processing**
   - User uploads same file twice
   - Worker crash during processing
   - Network timeout during upload

2. **Website Scraping**
   - Multiple chatbots scrape same URL
   - Retry after network failure
   - Scheduled scraping of same site

3. **Notifications**
   - User triggers same action multiple times
   - Retry after email service failure
   - Duplicate webhook calls

4. **Analytics Reports**
   - Multiple users request same report
   - Dashboard auto-refresh
   - Scheduled report generation

---

## 📞 Troubleshooting

### Issue: Task stuck with lock

**Symptom:** Task never executes, lock exists
```bash
redis-cli get "task_lock:backend.tasks.process_document:abc123"
```

**Solution:** Delete expired lock
```bash
redis-cli del "task_lock:backend.tasks.process_document:abc123"
```

### Issue: Cached result incorrect

**Symptom:** Task returns old result
```bash
redis-cli get "task_result:backend.tasks.process_document:abc123"
```

**Solution:** Clear cache for task
```bash
redis-cli del "task_result:backend.tasks.process_document:abc123"
```

### Issue: Too many retries

**Symptom:** Task fails repeatedly
```python
# Check task result
from celery.result import AsyncResult
result = AsyncResult('task-id')
print(result.traceback)  # See error details
```

**Solution:** Fix underlying issue or reduce max_retries

---

## ✅ Verification Checklist

- ✅ All tasks use IdempotentTask base class
- ✅ Redis connection working
- ✅ Task locks created on execution
- ✅ Results cached on success
- ✅ Locks released after completion
- ✅ Duplicate tasks skipped
- ✅ Retry with exponential backoff working
- ✅ Max retries respected
- ✅ Worker crash handling working
- ✅ Cache expiration working (1 hour)

---

## 🎉 Success!

Your Celery tasks now have comprehensive idempotency support with:
- **Deduplication** - No duplicate execution
- **Result Caching** - Fast repeated requests
- **Retry Logic** - Exponential backoff
- **Reliability** - Handles crashes gracefully
- **Scalability** - Works with multiple workers

All tasks are now production-ready and highly reliable! 🚀
