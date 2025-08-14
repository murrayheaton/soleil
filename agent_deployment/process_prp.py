#!/usr/bin/env python3
"""
Process PRPs through the Primary Orchestrator
Coordinates the multi-agent system to work on SOLEil development tasks
"""

import asyncio
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from primary_orchestrator import PrimaryOrchestratorAgent

async def process_authentication_prp():
    """Process the authentication system fix PRP"""
    print("🔐 Processing Authentication System Fix PRP...")
    
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
    
    # Monitor progress
    print("\n🔄 Monitoring agent progress...")
    for i in range(30):  # Monitor for 30 seconds
        await asyncio.sleep(1)
        
        status = orchestrator.get_status()
        print(f"Progress: {status['completed_tasks']}/{status['completed_tasks'] + status['active_tasks'] + status['queued_tasks']} tasks completed")
        
        if status['queued_tasks'] == 0 and status['active_tasks'] == 0:
            print("🎉 All tasks completed!")
            break
    
    # Get final status
    final_status = orchestrator.get_detailed_status()
    print(f"\n📊 Final Status:")
    print(f"  PRPs: {final_status['summary']['active_prps']}")
    print(f"  Tasks Completed: {final_status['summary']['completed_tasks']}")
    print(f"  Tasks Failed: {final_status['summary']['failed_tasks']}")
    
    return orchestrator

async def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Multi-Agent Development System                ║
    ║              PRP Processing & Coordination               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Process the authentication PRP
    orchestrator = await process_authentication_prp()
    
    print("\n🚀 Multi-agent system is now coordinating development tasks!")
    print("I'm your primary orchestrator agent, coordinating specialized agents in the background.")

if __name__ == "__main__":
    asyncio.run(main())
