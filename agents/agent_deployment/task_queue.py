"""
Task Queue System for Multi-Agent Communication
Uses RabbitMQ for message passing and Redis for result storage
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import aioredis
import aio_pika
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class TaskMessage:
    """Task message structure for queue"""
    task_id: str
    agent_type: str
    action: str
    payload: Dict[str, Any]
    priority: TaskPriority
    correlation_id: str
    timestamp: str
    retry_count: int = 0
    max_retries: int = 3


class TaskQueue:
    """Task queue manager for agent communication"""
    
    def __init__(self, rabbitmq_url: str = "amqp://soleil:soleil123@localhost/", 
                 redis_url: str = "redis://localhost"):
        self.rabbitmq_url = rabbitmq_url
        self.redis_url = redis_url
        self.connection = None
        self.channel = None
        self.redis = None
        self.exchanges = {}
        self.queues = {}
        
    async def connect(self):
        """Connect to RabbitMQ and Redis"""
        # Connect to RabbitMQ
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        
        # Set prefetch count for load balancing
        await self.channel.set_qos(prefetch_count=1)
        
        # Connect to Redis
        self.redis = await aioredis.create_redis_pool(self.redis_url)
        
        # Setup exchanges and queues
        await self._setup_exchanges()
        await self._setup_queues()
        
        logger.info("Task queue system connected")
    
    async def _setup_exchanges(self):
        """Setup message exchanges"""
        # Direct exchange for targeted agent messages
        self.exchanges['agents'] = await self.channel.declare_exchange(
            'soleil.agents',
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Topic exchange for broadcast messages
        self.exchanges['broadcast'] = await self.channel.declare_exchange(
            'soleil.broadcast',
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        # Priority exchange for urgent tasks
        self.exchanges['priority'] = await self.channel.declare_exchange(
            'soleil.priority',
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
    
    async def _setup_queues(self):
        """Setup agent queues"""
        agent_types = [
            'orchestrator', 'planning', 'frontend', 'backend',
            'database', 'security', 'unit_test', 'integration_test',
            'e2e_test', 'devops', 'code_review', 'documentation'
        ]
        
        for agent_type in agent_types:
            # Create queue with priority support
            queue = await self.channel.declare_queue(
                f'soleil.agent.{agent_type}',
                durable=True,
                arguments={
                    'x-max-priority': 10,
                    'x-message-ttl': 3600000  # 1 hour TTL
                }
            )
            
            # Bind to direct exchange
            await queue.bind(self.exchanges['agents'], routing_key=agent_type)
            
            # Bind to broadcast exchange with pattern
            await queue.bind(self.exchanges['broadcast'], routing_key=f'{agent_type}.*')
            await queue.bind(self.exchanges['broadcast'], routing_key='all.*')
            
            self.queues[agent_type] = queue
        
        # Create dead letter queue for failed messages
        dlq = await self.channel.declare_queue(
            'soleil.dlq',
            durable=True,
            arguments={'x-message-ttl': 86400000}  # 24 hour TTL
        )
        self.queues['dlq'] = dlq
    
    async def send_task(self, agent_type: str, action: str, 
                        payload: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Send task to specific agent"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        correlation_id = str(uuid.uuid4())
        
        message = TaskMessage(
            task_id=task_id,
            agent_type=agent_type,
            action=action,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
            timestamp=datetime.now().isoformat()
        )
        
        # Prepare message
        message_body = json.dumps(asdict(message)).encode()
        
        # Send with priority
        await self.exchanges['agents'].publish(
            aio_pika.Message(
                body=message_body,
                correlation_id=correlation_id,
                priority=priority.value,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=agent_type
        )
        
        # Store task metadata in Redis
        await self.redis.setex(
            f"task:{task_id}",
            3600,  # 1 hour expiry
            json.dumps({
                'status': 'sent',
                'agent': agent_type,
                'action': action,
                'timestamp': message.timestamp
            })
        )
        
        logger.info(f"Task {task_id} sent to {agent_type}")
        return task_id
    
    async def broadcast_message(self, pattern: str, message: Dict[str, Any]):
        """Broadcast message to multiple agents"""
        message_body = json.dumps(message).encode()
        
        await self.exchanges['broadcast'].publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=pattern
        )
        
        logger.info(f"Broadcast message sent with pattern: {pattern}")
    
    async def consume_tasks(self, agent_type: str, handler):
        """Consume tasks for specific agent"""
        queue = self.queues.get(agent_type)
        if not queue:
            raise ValueError(f"Queue not found for agent: {agent_type}")
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        # Parse message
                        task_data = json.loads(message.body.decode())
                        task = TaskMessage(**task_data)
                        
                        # Update status in Redis
                        await self.redis.setex(
                            f"task:{task.task_id}",
                            3600,
                            json.dumps({
                                'status': 'processing',
                                'agent': agent_type,
                                'started_at': datetime.now().isoformat()
                            })
                        )
                        
                        # Process task
                        result = await handler(task)
                        
                        # Store result in Redis
                        await self.redis.setex(
                            f"result:{task.task_id}",
                            3600,
                            json.dumps(result)
                        )
                        
                        # Update status
                        await self.redis.setex(
                            f"task:{task.task_id}",
                            3600,
                            json.dumps({
                                'status': 'completed',
                                'agent': agent_type,
                                'completed_at': datetime.now().isoformat()
                            })
                        )
                        
                        logger.info(f"Task {task.task_id} completed by {agent_type}")
                        
                    except Exception as e:
                        logger.error(f"Error processing task: {e}")
                        
                        # Handle retry logic
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            await self.send_task(
                                agent_type=task.agent_type,
                                action=task.action,
                                payload=task.payload,
                                priority=task.priority
                            )
                        else:
                            # Send to dead letter queue
                            await self._send_to_dlq(task, str(e))
    
    async def _send_to_dlq(self, task: TaskMessage, error: str):
        """Send failed task to dead letter queue"""
        dlq_message = {
            'task': asdict(task),
            'error': error,
            'failed_at': datetime.now().isoformat()
        }
        
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(dlq_message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key='soleil.dlq'
        )
        
        logger.error(f"Task {task.task_id} sent to DLQ: {error}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status from Redis"""
        status_data = await self.redis.get(f"task:{task_id}")
        if status_data:
            return json.loads(status_data)
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[Dict]:
        """Get task result from Redis"""
        result_data = await self.redis.get(f"result:{task_id}")
        if result_data:
            return json.loads(result_data)
        return None
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        stats = {}
        for agent_type, queue in self.queues.items():
            if agent_type != 'dlq':
                declaration = await queue.declare(passive=True)
                stats[agent_type] = declaration.message_count
        return stats
    
    async def close(self):
        """Close connections"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
        
        if self.connection:
            await self.connection.close()
        
        logger.info("Task queue system disconnected")


# Example agent handler
async def example_agent_handler(task: TaskMessage) -> Dict[str, Any]:
    """Example task handler for agents"""
    logger.info(f"Processing task: {task.task_id}")
    
    # Simulate task processing
    await asyncio.sleep(2)
    
    # Return result
    return {
        'status': 'success',
        'task_id': task.task_id,
        'processed_at': datetime.now().isoformat(),
        'result': f"Processed {task.action} successfully"
    }


# CLI for testing
async def main():
    """Test the task queue system"""
    queue = TaskQueue()
    await queue.connect()
    
    try:
        # Send test tasks
        task_id1 = await queue.send_task(
            'backend',
            'create_api_endpoint',
            {'endpoint': '/api/users', 'method': 'POST'},
            TaskPriority.HIGH
        )
        print(f"Sent task: {task_id1}")
        
        task_id2 = await queue.send_task(
            'frontend',
            'create_component',
            {'component': 'UserDashboard', 'props': ['user', 'stats']},
            TaskPriority.NORMAL
        )
        print(f"Sent task: {task_id2}")
        
        # Broadcast message
        await queue.broadcast_message(
            'all.status',
            {'message': 'System update', 'timestamp': datetime.now().isoformat()}
        )
        
        # Check queue stats
        stats = await queue.get_queue_stats()
        print(f"Queue stats: {stats}")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Check task status
        status1 = await queue.get_task_status(task_id1)
        print(f"Task {task_id1} status: {status1}")
        
    finally:
        await queue.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())