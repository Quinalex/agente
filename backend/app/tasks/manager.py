"""
Task manager with database and Redis integration.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.core.redis_client import get_redis
from app.core.config import settings
from app.tasks.models import TaskCreate, TaskResponse, TaskStatus, TaskUpdate
from app.tasks.models import Task  # SQLAlchemy model (to be created)

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages task lifecycle."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.redis = get_redis()

    async def create_task(self, task_create: TaskCreate) -> TaskResponse:
        \"\"\"Create a new task.\"\"\"
        task_id = str(uuid.uuid4())
        
        # Create in database
        task_data = {
            "id": task_id,
            "description": task_create.description,
            "priority": task_create.priority,
            "status": TaskStatus.PENDING.value,
            "llm_provider": task_create.llm_provider or settings.DEFAULT_LLM_PROVIDER,
            "max_retries": task_create.max_retries,
            "retry_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Store in Redis queue
        queue_key = f\"tasks:queue:{task_create.priority}\"
        await self.redis.lpush(queue_key, task_id)
        await self.redis.setex(
            f\"task:{task_id}\",
            settings.TASK_TTL_SECONDS,
            json.dumps(task_data, default=str),
        )

        logger.info(f\"Task created: {task_id}\")
        return TaskResponse(**task_data)

    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        \"\"\"Get task by ID.\"\"\"
        data = await self.redis.get(f\"task:{task_id}\")
        if not data:
            return None
        return TaskResponse(**json.loads(data))

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> List[TaskResponse]:
        \"\"\"List tasks.\"\"\"
        # Get all tasks from Redis
        keys = await self.redis.keys(\"task:*\")
        tasks = []

        for key in keys[skip : skip + limit]:
            data = await self.redis.get(key)
            if data:
                task = TaskResponse(**json.loads(data))
                if status is None or task.status == status:
                    tasks.append(task)

        return tasks

    async def cancel_task(self, task_id: str) -> bool:
        \"\"\"Cancel a task.\"\"\"
        data = await self.redis.get(f\"task:{task_id}\")
        if not data:
            return False

        task_data = json.loads(data)
        task_data[\"status\"] = TaskStatus.CANCELLED.value
        task_data[\"updated_at\"] = datetime.utcnow().isoformat()

        await self.redis.setex(
            f\"task:{task_id}\",
            settings.TASK_TTL_SECONDS,
            json.dumps(task_data, default=str),
        )

        logger.info(f\"Task cancelled: {task_id}\")
        return True

    async def get_stats(self) -> Dict[str, Any]:
        \"\"\"Get system statistics.\"\"\"
        all_tasks = await self.redis.keys(\"task:*\")
        tasks_count = len(all_tasks)

        pending = 0
        running = 0
        completed = 0
        failed = 0

        for key in all_tasks:
            data = await self.redis.get(key)
            if data:
                task = json.loads(data)
                if task[\"status\"] == TaskStatus.PENDING.value:
                    pending += 1
                elif task[\"status\"] == TaskStatus.RUNNING.value:
                    running += 1
                elif task[\"status\"] == TaskStatus.COMPLETED.value:
                    completed += 1
                elif task[\"status\"] == TaskStatus.FAILED.value:
                    failed += 1

        return {
            \"total_tasks\": tasks_count,
            \"pending\": pending,
            \"running\": running,
            \"completed\": completed,
            \"failed\": failed,
        }
", "path": "backend/app/tasks/manager.py", "repo": "agente", "owner": "Quinalex"}
