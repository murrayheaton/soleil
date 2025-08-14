#!/usr/bin/env python3
"""
Activate the Multi-Agent System
Start real development work on the authentication PRP
"""

import asyncio
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from primary_orchestrator import PrimaryOrchestratorAgent

async def activate_multi_agent_system():
    """Activate the multi-agent system to work on real development tasks"""
    print("🚀 Activating SOLEil Multi-Agent Development System...")
    
    # Initialize orchestrator
    orchestrator = PrimaryOrchestratorAgent()
    
    # Read the authentication PRP
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
    
    print(f"✅ PRP {prp.prp_id} activated with {len(prp.tasks)} tasks")
    print(f"🎯 Multi-agent system is now working on: {prp.title}")
    
    # Start task queue processor
    queue_processor = asyncio.create_task(orchestrator.process_task_queue())
    
    # Monitor progress in real-time
    print("\n🔄 Multi-Agent System Active - Monitoring Real Development Progress...")
    print("📊 Check the web dashboard at http://localhost:5001 for live updates")
    
    for i in range(120):  # Monitor for 2 minutes
        await asyncio.sleep(2)
        
        status = orchestrator.get_status()
        total_tasks = status['completed_tasks'] + status['active_tasks'] + status['queued_tasks']
        
        print(f"🔄 Progress: {status['completed_tasks']}/{total_tasks} completed | Active: {status['active_tasks']} | Queued: {status['queued_tasks']}")
        
        # Show what agents are currently working on
        if status['active_tasks'] > 0:
            detailed_status = orchestrator.get_detailed_status()
            active_tasks = [task_id for task_id, task_info in detailed_status['tasks'].items() 
                           if task_info['status'] == 'in_progress']
            if active_tasks:
                print(f"  🔄 Active agents: {', '.join(active_tasks[:3])}{'...' if len(active_tasks) > 3 else ''}")
        
        # Exit if all tasks complete
        if status['completed_tasks'] == total_tasks and total_tasks > 0:
            print("🎉 All tasks completed!")
            break
    
    # Final status
    final_status = orchestrator.get_detailed_status()
    print(f"\n📊 Multi-Agent System Final Status:")
    print(f"  PRPs: {final_status['summary']['active_prps']}")
    print(f"  Tasks Completed: {final_status['summary']['completed_tasks']}")
    print(f"  Tasks Failed: {final_status['summary']['failed_tasks']}")
    
    return orchestrator

async def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Multi-Agent Development System                ║
    ║              ACTIVATION & REAL DEVELOPMENT               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Activate the multi-agent system
    orchestrator = await activate_multi_agent_system()
    
    print("\n🚀 Multi-agent system is now actively developing!")
    print("🔍 The web dashboard shows real-time file changes and progress")
    print("🤖 Specialized agents are working in parallel on the authentication system")

if __name__ == "__main__":
    asyncio.run(main())
