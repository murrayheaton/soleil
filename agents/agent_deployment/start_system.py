#!/usr/bin/env python3
"""
Start the SOLEil Multi-Agent Development System
This script initializes the orchestrator and processes PRPs
"""

import asyncio
import sys
import json
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import OrchestratorAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_deployment/logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def process_prp_file(orchestrator: OrchestratorAgent, prp_path: Path):
    """Process a PRP file through the system"""
    logger.info(f"Processing PRP: {prp_path.name}")
    
    # Read PRP content
    with open(prp_path, 'r') as f:
        content = f.read()
    
    # Parse PRP (simplified - in production would have proper parser)
    prp_data = {
        'title': 'Offline Chart Viewer',
        'description': content[:500],  # First 500 chars as description
        'full_content': content,
        'source_file': str(prp_path)
    }
    
    # Send to orchestrator
    prp = await orchestrator.receive_prp(prp_data)
    
    logger.info(f"PRP {prp.prp_id} created with {len(prp.tasks)} tasks")
    return prp


async def monitor_system(orchestrator: OrchestratorAgent):
    """Monitor system status periodically"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        status = orchestrator.get_status()
        logger.info(f"""
System Status:
- Active PRPs: {status['active_prps']}
- Active Tasks: {status['active_tasks']}
- Queued Tasks: {status['queued_tasks']}
- Completed: {status['completed_tasks']}
- Failed: {status['failed_tasks']}
        """)
        
        # Check if system is idle and has work
        if status['active_tasks'] == 0 and status['queued_tasks'] == 0 and status['active_prps'] > 0:
            logger.warning("System appears idle with active PRPs - checking for stuck tasks")


async def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Multi-Agent Development System - Phase 3      ║
    ║                   Production Rollout                      ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Starting system components...
    """)
    
    # Create necessary directories
    Path("agent_deployment/logs").mkdir(parents=True, exist_ok=True)
    Path("agent_deployment/reports").mkdir(parents=True, exist_ok=True)
    Path("agent_deployment/metrics").mkdir(parents=True, exist_ok=True)
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Start orchestrator in background
    orchestrator_task = asyncio.create_task(orchestrator.start())
    
    # Start system monitor
    monitor_task = asyncio.create_task(monitor_system(orchestrator))
    
    # Wait for system to initialize
    await asyncio.sleep(2)
    
    print("""
    ✅ System initialized successfully!
    
    Available Commands:
    - status: Show system status
    - prp <file>: Process a PRP file
    - metrics: Show performance metrics
    - quit: Shutdown system
    """)
    
    # Check for active PRPs to process
    active_prp_dir = Path("PRPs/active")
    if active_prp_dir.exists():
        prp_files = list(active_prp_dir.glob("*.md"))
        if prp_files:
            print(f"\n📋 Found {len(prp_files)} active PRP(s) to process:")
            for prp_file in prp_files:
                print(f"  - {prp_file.name}")
            
            # Process first PRP as demonstration
            if prp_files:
                print(f"\n🚀 Processing: {prp_files[0].name}")
                await process_prp_file(orchestrator, prp_files[0])
    
    # Interactive command loop
    try:
        while True:
            try:
                # Non-blocking input check
                await asyncio.sleep(1)
                
                # In production, this would be replaced with proper async input handling
                # For now, just let the system run
                
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        logger.error(f"System error: {e}")
    
    finally:
        print("\n🛑 Shutting down system...")
        
        # Cancel background tasks
        orchestrator_task.cancel()
        monitor_task.cancel()
        
        # Wait for cleanup
        await asyncio.gather(orchestrator_task, monitor_task, return_exceptions=True)
        
        # Generate final report
        status = orchestrator.get_status()
        report = {
            'shutdown_time': datetime.now().isoformat(),
            'final_status': status,
            'session_summary': {
                'total_completed': status['completed_tasks'],
                'total_failed': status['failed_tasks'],
                'active_at_shutdown': status['active_tasks']
            }
        }
        
        report_path = Path(f"agent_deployment/reports/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Session report saved to: {report_path}")
        print("👋 System shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ System interrupted by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        sys.exit(1)