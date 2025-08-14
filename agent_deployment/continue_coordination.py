#!/usr/bin/env python3
"""
Continue coordinating the multi-agent system
Process remaining tasks and monitor progress
"""

import asyncio
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from primary_orchestrator import PrimaryOrchestratorAgent

async def continue_coordination():
    """Continue coordinating the agents"""
    print("🔄 Continuing Multi-Agent Coordination...")
    
    # Initialize orchestrator
    orchestrator = PrimaryOrchestratorAgent()
    
    # Read the PRP content again to recreate the state
    prp_path = Path("PRPs/active/PRP_11_fix_authentication_system.md")
    with open(prp_path, 'r') as f:
        prp_content = f.read()
    
    # Create PRP data
    prp_data = {
        'title': 'Fix Authentication System - Complete Overhaul',
        'description': 'Critical authentication issues preventing users from using the application after OAuth login',
        'full_content': prp_content
    }
    
    # Send to orchestrator
    prp = await orchestrator.receive_prp(prp_data)
    
    print(f"✅ PRP {prp.prp_id} recreated with {len(prp.tasks)} tasks")
    
    # Start task queue processor
    queue_processor = asyncio.create_task(orchestrator.process_task_queue())
    
    # Monitor progress for longer to see all tasks complete
    print("\n🔄 Monitoring agent progress for complete execution...")
    for i in range(60):  # Monitor for 60 seconds
        await asyncio.sleep(1)
        
        status = orchestrator.get_status()
        total_tasks = status['completed_tasks'] + status['active_tasks'] + status['queued_tasks']
        
        print(f"Progress: {status['completed_tasks']}/{total_tasks} tasks completed | Active: {status['active_tasks']} | Queued: {status['queued_tasks']}")
        
        if status['queued_tasks'] == 0 and status['active_tasks'] == 0:
            print("🎉 All tasks completed!")
            break
    
    # Get final status
    final_status = orchestrator.get_detailed_status()
    print(f"\n📊 Final Status:")
    print(f"  PRPs: {final_status['summary']['active_prps']}")
    print(f"  Tasks Completed: {final_status['summary']['completed_tasks']}")
    print(f"  Tasks Failed: {final_status['summary']['failed_tasks']}")
    
    # Show task details
    print(f"\n📋 Task Details:")
    for task_id, task_info in final_status['tasks'].items():
        print(f"  {task_id}: {task_info['description']}")
        print(f"    Status: {task_info['status']} | Agent: {task_info['agent']}")
    
    return orchestrator

async def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Multi-Agent Development System                ║
    ║              Continued Coordination                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Continue coordination
    orchestrator = await continue_coordination()
    
    print("\n🚀 Multi-agent coordination completed!")
    print("All specialized agents have been coordinated to work on the authentication system fix.")

if __name__ == "__main__":
    asyncio.run(main())
