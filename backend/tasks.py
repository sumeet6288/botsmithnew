from celery import Task
from backend.celery_app import celery_app
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base task class that properly handles async functions"""
    def __call__(self, *args, **kwargs):
        # Create new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._run_async(*args, **kwargs))
        finally:
            loop.close()
    
    async def _run_async(self, *args, **kwargs):
        return await self.run(*args, **kwargs)


@celery_app.task(name='backend.tasks.process_document', bind=True)
def process_document(self, source_id: str, file_path: str, chatbot_id: str) -> Dict[str, Any]:
    """
    Background task to process uploaded documents
    
    Args:
        source_id: Source document ID
        file_path: Path to uploaded file
        chatbot_id: Associated chatbot ID
    
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Processing document: {source_id}")
        
        # Import here to avoid circular imports
        from services.document_processor import DocumentProcessor
        from services.chunking_service import ChunkingService
        from models import get_database
        
        # Get database
        db = get_database()
        
        # Process the document
        processor = DocumentProcessor()
        text_content = processor.process_file(file_path)
        
        # Chunk the content
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_text(text_content)
        
        # Store chunks in database
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_doc = {
                'chatbot_id': chatbot_id,
                'source_id': source_id,
                'content': chunk,
                'chunk_index': i,
                'metadata': {'total_chunks': len(chunks)}
            }
            chunk_docs.append(chunk_doc)
        
        if chunk_docs:
            db.chunks.insert_many(chunk_docs)
        
        # Update source status
        db.sources.update_one(
            {'_id': source_id},
            {'$set': {'status': 'completed', 'chunk_count': len(chunks)}}
        )
        
        logger.info(f"Document processed successfully: {source_id} ({len(chunks)} chunks)")
        return {
            'status': 'success',
            'source_id': source_id,
            'chunks_created': len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error processing document {source_id}: {str(e)}")
        # Update source with error status
        try:
            from models import get_database
            db = get_database()
            db.sources.update_one(
                {'_id': source_id},
                {'$set': {'status': 'failed', 'error': str(e)}}
            )
        except:
            pass
        
        raise


@celery_app.task(name='backend.tasks.scrape_website', bind=True)
def scrape_website(self, source_id: str, url: str, chatbot_id: str) -> Dict[str, Any]:
    """
    Background task to scrape website content
    
    Args:
        source_id: Source ID
        url: Website URL to scrape
        chatbot_id: Associated chatbot ID
    
    Returns:
        Dict with scraping results
    """
    try:
        logger.info(f"Scraping website: {url}")
        
        # Import here to avoid circular imports
        from services.website_scraper import WebsiteScraper
        from services.chunking_service import ChunkingService
        from models import get_database
        
        # Get database
        db = get_database()
        
        # Scrape the website
        scraper = WebsiteScraper()
        content = scraper.scrape(url)
        
        # Chunk the content
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_text(content)
        
        # Store chunks in database
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_doc = {
                'chatbot_id': chatbot_id,
                'source_id': source_id,
                'content': chunk,
                'chunk_index': i,
                'metadata': {'url': url, 'total_chunks': len(chunks)}
            }
            chunk_docs.append(chunk_doc)
        
        if chunk_docs:
            db.chunks.insert_many(chunk_docs)
        
        # Update source status
        db.sources.update_one(
            {'_id': source_id},
            {'$set': {'status': 'completed', 'chunk_count': len(chunks)}}
        )
        
        logger.info(f"Website scraped successfully: {url} ({len(chunks)} chunks)")
        return {
            'status': 'success',
            'source_id': source_id,
            'url': url,
            'chunks_created': len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error scraping website {url}: {str(e)}")
        # Update source with error status
        try:
            from models import get_database
            db = get_database()
            db.sources.update_one(
                {'_id': source_id},
                {'$set': {'status': 'failed', 'error': str(e)}}
            )
        except:
            pass
        
        raise


@celery_app.task(name='backend.tasks.send_notification')
def send_notification(user_id: str, title: str, message: str, notification_type: str = 'info') -> Dict[str, Any]:
    """
    Background task to send notifications
    
    Args:
        user_id: Target user ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification
    
    Returns:
        Dict with notification results
    """
    try:
        logger.info(f"Sending notification to user: {user_id}")
        
        from models import get_database
        from datetime import datetime
        
        db = get_database()
        
        # Create notification document
        notification = {
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': notification_type,
            'read': False,
            'created_at': datetime.utcnow(),
        }
        
        # Insert into database
        result = db.notifications.insert_one(notification)
        
        logger.info(f"Notification sent successfully to user: {user_id}")
        return {
            'status': 'success',
            'notification_id': str(result.inserted_id),
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"Error sending notification to {user_id}: {str(e)}")
        raise


@celery_app.task(name='backend.tasks.cleanup_old_data')
def cleanup_old_data(days: int = 90) -> Dict[str, Any]:
    """
    Background task to cleanup old data
    
    Args:
        days: Number of days to keep data
    
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Cleaning up data older than {days} days")
        
        from models import get_database
        from datetime import datetime, timedelta
        
        db = get_database()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Cleanup old messages
        messages_result = db.messages.delete_many(
            {'created_at': {'$lt': cutoff_date}}
        )
        
        # Cleanup old conversations without messages
        conversations_result = db.conversations.delete_many({
            'updated_at': {'$lt': cutoff_date},
            'message_count': 0
        })
        
        logger.info(f"Cleanup completed: {messages_result.deleted_count} messages, {conversations_result.deleted_count} conversations")
        return {
            'status': 'success',
            'messages_deleted': messages_result.deleted_count,
            'conversations_deleted': conversations_result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise


@celery_app.task(name='backend.tasks.generate_analytics_report')
def generate_analytics_report(chatbot_id: str, period: str = '30d') -> Dict[str, Any]:
    """
    Background task to generate comprehensive analytics reports
    
    Args:
        chatbot_id: Chatbot ID
        period: Time period for report
    
    Returns:
        Dict with report data
    """
    try:
        logger.info(f"Generating analytics report for chatbot: {chatbot_id}")
        
        from models import get_database
        from datetime import datetime, timedelta
        
        db = get_database()
        
        # Calculate date range
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Aggregate data
        total_conversations = db.conversations.count_documents({
            'chatbot_id': chatbot_id,
            'created_at': {'$gte': start_date}
        })
        
        total_messages = db.messages.count_documents({
            'chatbot_id': chatbot_id,
            'created_at': {'$gte': start_date}
        })
        
        # Average response time
        avg_response_pipeline = [
            {'$match': {
                'chatbot_id': chatbot_id,
                'created_at': {'$gte': start_date},
                'response_time': {'$exists': True}
            }},
            {'$group': {
                '_id': None,
                'avg_response_time': {'$avg': '$response_time'}
            }}
        ]
        
        avg_response = list(db.messages.aggregate(avg_response_pipeline))
        avg_response_time = avg_response[0]['avg_response_time'] if avg_response else 0
        
        report = {
            'chatbot_id': chatbot_id,
            'period': period,
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'avg_response_time': round(avg_response_time, 2),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Analytics report generated for chatbot: {chatbot_id}")
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics report for {chatbot_id}: {str(e)}")
        raise
