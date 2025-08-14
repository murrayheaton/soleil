#!/usr/bin/env python3
"""
Debug script to inspect orchestrator state and fix stuck tasks
"""

import asyncio
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import OrchestratorAgent, TaskStatus

async def debug_orchestrator():
    """Debug the orchestrator state"""
    print("🔍 Debugging SOLEil Orchestrator State...")
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Get current status
    status = orchestrator.get_status()
    print(f"\n📊 Current Status:")
    print(f"  Active PRPs: {status['active_prps']}")
    print(f"  Active Tasks: {status['active_tasks']}")
    print(f"  Queued Tasks: {status['queued_tasks']}")
    print(f"  Completed: {status['completed_tasks']}")
    print(f"  Failed: {status['failed_tasks']}")
    
    print(f"\n🤖 Agent Status:")
    for agent, agent_status in status['agent_status'].items():
        print(f"  {agent}: {agent_status}")
    
    print(f"\n📋 Task Queue Details:")
    if orchestrator.task_queue:
        for i, task in enumerate(orchestrator.task_queue):
            print(f"  {i+1}. {task.task_id} - {task.description[:50]}...")
            print(f"     Status: {task.status.value}")
            print(f"     Agent: {task.agent_type.value}")
            print(f"     Priority: {task.priority}")
    else:
        print("  No tasks in queue")
    
    print(f"\n🔄 Active Tasks Details:")
    if orchestrator.active_tasks:
        for task_id, task in orchestrator.active_tasks.items():
            print(f"  {task_id}: {task.description[:50]}...")
            print(f"     Status: {task.status.value}")
            print(f"     Agent: {task.agent_type.value}")
    else:
        print("  No active tasks")
    
    print(f"\n📁 Active PRPs:")
    if orchestrator.active_prps:
        for prp_id, prp in orchestrator.active_prps.items():
            print(f"  {prp_id}: {prp.title}")
            print(f"     Status: {prp.status.value}")
            print(f"     Tasks: {len(prp.tasks)}")
    else:
        print("  No active PRPs")

if __name__ == "__main__":
    asyncio.run(debug_orchestrator())
