import aio_pika
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class RabbitMQClient:
    """Client for interacting with RabbitMQ."""
    
    def __init__(
        self, 
        host: str, 
        port: int, 
        username: str, 
        password: str, 
        queue_name: str,
        heartbeat: int = 60,
        connection_timeout: float = 10.0
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue_name = queue_name
        self.heartbeat = heartbeat
        self.connection_timeout = connection_timeout
        self.connection = None
        self.channel = None
    
    async def connect(self, max_retries: int = 3) -> bool:
        """
        Establish connection to RabbitMQ with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if connection was successful, False otherwise
        """
        retry_count = 0
        retry_delay = 2  # seconds
        
        while retry_count <= max_retries:
            try:
                self.connection = await aio_pika.connect_robust(
                    host=self.host,
                    port=self.port,
                    login=self.username,
                    password=self.password,
                    heartbeat=self.heartbeat,
                    timeout=self.connection_timeout
                )
                
                self.channel = await self.connection.channel()
                await self.channel.declare_queue(self.queue_name, durable=True)
                
                logger.info("Successfully connected to RabbitMQ")
                return True
                
            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(
                        f"RabbitMQ connection attempt {retry_count} failed: {e}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {e}")
                    break
        
        return False
    
    async def publish_message(self, message: Dict[str, Any]) -> bool:
        """
        Publish a message to the configured queue.
        
        Args:
            message: The message to publish
            
        Returns:
            True if successfully published, False otherwise
        """
        if not self.connection or self.connection.is_closed:
            logger.error("Cannot publish message: RabbitMQ connection is not established")
            return False
            
        try:
            # Convert dict to JSON string for the message body
            message_body = json.dumps(message, default=str)  # Use default=str to handle datetime etc.
            
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=self.queue_name
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")
            return False
    
    async def close(self) -> None:
        """Close the RabbitMQ connection gracefully."""
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection: {e}")
                
    async def __aenter__(self):
        """Support for async context manager."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context manager."""
        await self.close() 