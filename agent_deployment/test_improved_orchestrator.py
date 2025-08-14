#!/usr/bin/env python3
"""
Test the improved orchestrator with proper dependency resolution
"""

import asyncio
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from primary_orchestrator import PrimaryOrchestratorAgent

async def test_dependency_resolution():
    """Test that tasks are properly unblocked when dependencies complete"""
    print("🧪 Testing Improved Orchestrator with Dependency Resolution...")
    
    # Initialize orchestrator
    orchestrator = PrimaryOrchestratorAgent()
    
    # Read the PRP content
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
    
    print(f"✅ PRP {prp.prp_id} created with {len(prp.tasks)} tasks")
    
    # Start task queue processor
    queue_processor = asyncio.create_task(orchestrator.process_task_queue())
    
    # Monitor progress with detailed status updates
    print("\n🔄 Monitoring agent progress with dependency resolution...")
    for i in range(90):  # Monitor for 90 seconds to see all tasks complete
        await asyncio.sleep(1)
        
        status = orchestrator.get_status()
        total_tasks = status['completed_tasks'] + status['active_tasks'] + status['queued_tasks']
        
        # Get detailed status for blocked tasks
        detailed_status = orchestrator.get_detailed_status()
        blocked_tasks = [task_id for task_id, task_info in detailed_status['tasks'].items() 
                        if task_info['status'] == 'blocked']
        
        print(f"Progress: {status['completed_tasks']}/{total_tasks} completed | Active: {status['active_tasks']} | Queued: {status['queued_tasks']} | Blocked: {len(blocked_tasks)}")
        
        # Only exit if all tasks are actually completed
        if status['completed_tasks'] == total_tasks and total_tasks > 0:
            print("🎉 All tasks completed!")
            break
        
        # Show blocked tasks every 10 seconds
        if i % 10 == 0 and blocked_tasks:
            print(f"  🔒 Blocked tasks: {', '.join(blocked_tasks[:3])}{'...' if len(blocked_tasks) > 3 else ''}")
        
        # Show active tasks every 5 seconds
        if i % 5 == 0 and status['active_tasks'] > 0:
            active_tasks = [task_id for task_id, task_info in detailed_status['tasks'].items() 
                           if task_info['status'] == 'in_progress']
            print(f"  🔄 Active tasks: {', '.join(active_tasks[:2])}{'...' if len(active_tasks) > 2 else ''}")
    
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
    ║              Improved Orchestrator Test                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test the improved orchestrator
    orchestrator = await test_dependency_resolution()
    
    print("\n🚀 Improved orchestrator test completed!")
    print("The system should now properly handle task dependencies and unblock tasks when ready.")

if __name__ == "__main__":
    asyncio.run(main())
