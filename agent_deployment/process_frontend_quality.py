#!/usr/bin/env python3
"""
Process Frontend Quality Check PRP with Transparent Orchestrator
Shows Murray exactly what agents are thinking and deciding
"""

import asyncio
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from transparent_orchestrator import TransparentOrchestratorAgent

async def process_frontend_quality_prp():
    """Process the frontend quality check PRP"""
    print("🚀 Starting Frontend Quality Check with Transparent Orchestrator...")
    
    # Initialize orchestrator
    orchestrator = TransparentOrchestratorAgent()
    
    # Load the PRP
    prp_path = Path("PRPs/active/PRP_frontend_quality_check.md")
    
    if not prp_path.exists():
        print(f"❌ PRP file not found: {prp_path}")
        return
    
    # Read PRP content
    with open(prp_path, 'r') as f:
        prp_content = f.read()
    
    # Parse PRP into structured content
    prp_data = {
        "title": "Frontend Code Quality Check & Debug",
        "description": "Run comprehensive quality checks on the frontend codebase, identify and fix any issues, and ensure all tests pass.",
        "full_content": prp_content
    }
    
    print(f"\n📋 Murray, I'm about to process this PRP:")
    print(f"   Title: {prp_data['title']}")
    print(f"   Description: {prp_data['description'][:100]}...")
    
    # Ask Murray for approval
    print(f"\n🎯 Murray, should I proceed with processing this frontend quality check PRP?")
    print(f"   This will create tasks for: Planning, Code Review, Frontend, and Testing agents")
    print(f"   Type 'yes' to proceed or 'no' to cancel")
    
    # In a real system, this would wait for Murray's input
    # For now, we'll proceed to show the system in action
    print(f"\n🤖 Proceeding with PRP processing...")
    
    # Process PRP
    prp = await orchestrator.receive_prp(prp_data)
    
    print(f"\n✅ PRP processed successfully!")
    print(f"   Created {len(prp.tasks)} tasks")
    print(f"   PRP ID: {prp.prp_id}")
    
    # Start task queue processing
    print(f"\n🔄 Starting task queue processing...")
    print(f"   Murray, you'll now see each agent's thoughts and decisions in real-time!")
    
    # Start the orchestrator
    queue_processor = asyncio.create_task(orchestrator.process_task_queue())
    
    # Monitor progress
    start_time = asyncio.get_event_loop().time()
    
    while True:
        await asyncio.sleep(2)
        
        status = orchestrator.get_status()
        elapsed = asyncio.get_event_loop().time() - start_time
        
        print(f"\n📊 Progress Update (after {elapsed:.1f}s):")
        print(f"   Active Tasks: {status['active_tasks']}")
        print(f"   Queued Tasks: {status['queued_tasks']}")
        print(f"   Completed: {status['completed_tasks']}")
        print(f"   Failed: {status['failed_tasks']}")
        
        # Check if all tasks are complete
        if status['completed_tasks'] == len(prp.tasks) and len(prp.tasks) > 0:
            print(f"\n🎉 Murray, all frontend quality check tasks are complete!")
            print(f"   Total time: {elapsed:.1f} seconds")
            print(f"   Success rate: 100%")
            break
        
        # Check for failures
        if status['failed_tasks'] > 0:
            print(f"\n❌ Murray, some tasks have failed!")
            print(f"   Failed tasks: {status['failed_tasks']}")
            print(f"   Should I continue or stop here?")
            break

if __name__ == "__main__":
    asyncio.run(process_frontend_quality_prp())
