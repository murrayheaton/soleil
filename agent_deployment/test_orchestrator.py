#!/usr/bin/env python3
"""
Simple test script to isolate orchestrator hanging issue
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from transparent_orchestrator import TransparentOrchestratorAgent

async def test_basic():
    """Test basic orchestrator functionality"""
    print("🧪 Testing basic orchestrator...")
    
    try:
        # Initialize orchestrator
        print("1. Creating orchestrator...")
        orchestrator = TransparentOrchestratorAgent()
        print("✅ Orchestrator created")
        
        # Test simple PRP
        print("2. Testing simple PRP...")
        test_prp = {
            "title": "Test PRP",
            "description": "This is a test PRP for Google Drive integration",
            "content": "Connect Google Drive services to API endpoints"
        }
        
        print("3. Calling receive_prp...")
        prp = await orchestrator.receive_prp(test_prp)
        print(f"✅ PRP received: {prp.prp_id}")
        
        print("4. Getting status...")
        status = orchestrator.get_status()
        print(f"✅ Status: {status}")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Transparent Orchestrator")
    print("=" * 50)
    
    asyncio.run(test_basic())
