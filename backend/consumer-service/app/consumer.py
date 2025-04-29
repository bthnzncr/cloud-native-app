import pika
import json
import logging
import asyncio
import signal  # For graceful shutdown
import time
from datetime import datetime, timedelta, timezone

import dateutil.parser  # For parsing ISO dates robustly
from motor.motor_asyncio import AsyncIOMotorClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import settings
from .db import get_article_collection, close_db, connect_db
from .filtered_categorizer import categorize_article, get_category_probabilities

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get values from settings
SIMILARITY_THRESHOLD = settings.SIMILARITY_THRESHOLD
DEDUPLICATION_WINDOW_HOURS = settings.DEDUPLICATION_WINDOW_HOURS

# Global flag for shutdown
shutdown_requested = False
rabbitmq_connection = None
rabbitmq_channel = None
db_client = None

# --- Similarity Calculation ---
def check_similarity(new_text: str, stored_texts: list) -> tuple:
    """Calculates TF-IDF vectors and cosine similarity between texts."""
    if not new_text or not stored_texts or all(not text for text in stored_texts):
        return [], 0.0
    
    tfidf = TfidfVectorizer(stop_words='english')
    # Combine all texts for fitting
    all_texts = [new_text] + stored_texts
    tfidf_matrix = tfidf.fit_transform(all_texts)
    
    # Get similarity scores between new text and each stored text
    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    return similarity_scores.flatten(), SIMILARITY_THRESHOLD

# --- Categorization ---
def categorize_news_article(article_data: dict) -> str:
    """Categorizes article using ML model."""
    text = f"{article_data.get('title', '')} {article_data.get('description', '')}"
    
    # Get category from ML model
    category = categorize_article(text)
    
    # Log probabilities for monitoring
    probs = get_category_probabilities(text)
    if probs:
        prob_info = ", ".join([f"{cat}: {prob:.2f}" for cat, prob in probs[:3]])
        logger.info(f"Article categorized as '{category}' [probabilities: {prob_info}]")
    
    return category

# --- Database Operations ---
async def check_and_save_article(article_data: dict):
    """Checks for duplicates and saves the article if unique."""
    global db_client
    if not db_client:
        logger.error('Database client not initialized.')
        return False

    collection = get_article_collection(db_client)

    link = article_data.get('link')
    if not link:
        logger.warning('Article data missing link.')
        return False

    # --- 1. Basic Link Check ---
    try:
        existing_by_link = await collection.find_one({'link': link})
        if existing_by_link:
            logger.info(f"Article already exists (link match): {link}")
            return True
    except Exception as e:
        logger.error(f"Error checking link existence: {e}")
        return False

    # --- 2. Similarity Check ---
    is_duplicate = False
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=DEDUPLICATION_WINDOW_HOURS)
        query = {
            'source': article_data.get('source'),
            'published_date': {'$gte': cutoff_time}
        }
        projection = {'title': 1, 'description': 1, 'link': 1}

        stored_titles = []
        stored_descriptions = []
        stored_articles = []
        
        async for recent_article in collection.find(query, projection):
            stored_titles.append(recent_article.get('title', ''))
            stored_descriptions.append(recent_article.get('description', ''))
            stored_articles.append(recent_article)
        
        incoming_title = article_data.get('title', '')
        title_similarities, _ = check_similarity(incoming_title, stored_titles)
        
        incoming_desc = article_data.get('description', '')
        desc_similarities, _ = check_similarity(incoming_desc, stored_descriptions)
        
        for i in range(len(stored_articles)):
            title_sim = title_similarities[i] if i < len(title_similarities) else 0
            desc_sim = desc_similarities[i] if i < len(desc_similarities) else 0
            
            combined_similarity = max(title_sim, desc_sim)
            
            if combined_similarity >= SIMILARITY_THRESHOLD:
                logger.info(f"Article deemed duplicate (similarity: {combined_similarity:.2f}): {link}")
                is_duplicate = True
                break

    except Exception as e:
        logger.error(f"Error during similarity check: {e}", exc_info=True)
        return False

    # --- 3. Add ML Category and Save ---
    if not is_duplicate:
        try:
            # Skip articles with null title or description
            if article_data.get('title') is None or article_data.get('description') is None:
                logger.warning(f"Skipping article with null title or description: {link}")
                return True
                
            # Save original category if present
            if 'category' in article_data:
                article_data['original_category'] = article_data['category']
            
            # Always apply ML categorization
            article_data['category'] = categorize_news_article(article_data)
            
            # Save to database
            result = await collection.update_one(
                {'link': link},
                {'$setOnInsert': article_data},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Saved new article with category '{article_data.get('category')}': {link}")
            else:
                logger.info(f"Article already exists (race condition): {link}")
            return True

        except Exception as e:
            logger.error(f"Error saving article to DB: {e}", exc_info=True)
            return False
    else:
        return True  # Duplicate found, handled successfully

# --- RabbitMQ Callback ---
def message_callback(ch, method, properties, body):
    """Processes a message received from RabbitMQ."""
    delivery_tag = method.delivery_tag
    logger.info(f"Received message {delivery_tag}")
    try:
        article_payload = json.loads(body)
        link = article_payload.get('link', 'UNKNOWN')

        # Validate required fields
        required_fields = ['link', 'title', 'published_date', 'fetched_at', 'source']
        if not all(field in article_payload for field in required_fields) or not article_payload['link']:
            logger.warning(f"Skipping message due to missing required fields: {link}")
            ch.basic_ack(delivery_tag=delivery_tag)
            return
            
        # Skip articles with null title or description
        if article_payload.get('title') is None or article_payload.get('description') is None:
            logger.warning(f"Skipping message with null title or description: {link}")
            ch.basic_ack(delivery_tag=delivery_tag)
            return

        # Parse dates
        try:
            parsed_data = article_payload.copy()
            parsed_data['published_date'] = dateutil.parser.isoparse(article_payload['published_date'])
            parsed_data['fetched_at'] = dateutil.parser.isoparse(article_payload['fetched_at'])
            parsed_data['published_date'] = parsed_data['published_date'].astimezone(timezone.utc)
            parsed_data['fetched_at'] = parsed_data['fetched_at'].astimezone(timezone.utc)
            
            # Save original category if present
            if 'category' in parsed_data:
                parsed_data['original_category'] = parsed_data['category']
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error parsing dates: {e}")
            ch.basic_ack(delivery_tag=delivery_tag)
            return

        # Process article
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(check_and_save_article(parsed_data))

        # Acknowledge message
        if success:
            logger.info(f"Successfully processed message: {link}")
            ch.basic_ack(delivery_tag=delivery_tag)
        else:
            logger.warning(f"Failed to process message: {link}")
            ch.basic_nack(delivery_tag=delivery_tag, requeue=False)

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON for message {delivery_tag}")
        ch.basic_ack(delivery_tag=delivery_tag)
    except Exception as e:
        logger.exception(f"Error processing message {delivery_tag}: {e}")
        try:
            ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        except Exception as ack_err:
            logger.error(f"Failed to Nack message {delivery_tag}: {ack_err}")

# --- Graceful Shutdown ---
def request_shutdown(sig, frame):
    """Handles shutdown signals."""
    global shutdown_requested
    logger.info(f"Shutdown requested (Signal: {sig}).")
    shutdown_requested = True
    if rabbitmq_channel:
        try:
            rabbitmq_channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error stopping consumption: {e}")
    if rabbitmq_connection and rabbitmq_connection.is_open:
        rabbitmq_connection.close()
        logger.info("RabbitMQ connection close initiated.")

# --- Main Function ---
def main():
    """Main function to setup and run the consumer."""
    global rabbitmq_connection, rabbitmq_channel, db_client
    global shutdown_requested
    
    shutdown_requested = False
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    # Initialize ML model
    logger.info("Initializing news categorizer model...")
    from .filtered_categorizer import filtered_categorizer
    
    # Connect to Database
    try:
        logger.info("Connecting to MongoDB...")
        loop = asyncio.get_event_loop()
        db_client = loop.run_until_complete(connect_db())
        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}. Exiting.")
        return

    # Connect to RabbitMQ
    logger.info("Connecting to RabbitMQ...")
    credentials = pika.PlainCredentials(settings.RABBITMQ_DEFAULT_USER, settings.RABBITMQ_DEFAULT_PASS)
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    while not shutdown_requested:
        try:
            rabbitmq_connection = pika.BlockingConnection(parameters)
            rabbitmq_channel = rabbitmq_connection.channel()

            rabbitmq_channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
            logger.info(f"Declared queue: {settings.RABBITMQ_QUEUE}")

            rabbitmq_channel.basic_qos(prefetch_count=1)
            rabbitmq_channel.basic_consume(
                queue=settings.RABBITMQ_QUEUE,
                on_message_callback=message_callback
            )

            logger.info("Consumer started. Waiting for messages...")
            rabbitmq_channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ connection error: {e}. Retrying in 5 seconds...")
            if rabbitmq_connection and rabbitmq_connection.is_open:
                try:
                    rabbitmq_connection.close()
                except Exception:
                    pass
            time.sleep(5)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            shutdown_requested = True
        finally:
            if rabbitmq_connection and rabbitmq_connection.is_open:
                try:
                    rabbitmq_connection.close()
                except Exception:
                    pass
            logger.info("RabbitMQ connection closed.")

    # Cleanup
    logger.info("Shutting down...")
    if rabbitmq_connection and rabbitmq_connection.is_open:
        try:
            rabbitmq_connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

    if db_client:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_db(db_client))
        logger.info("MongoDB connection closed.")

    logger.info("Consumer stopped.")

if __name__ == "__main__":
    main() 