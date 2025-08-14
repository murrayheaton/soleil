#!/usr/bin/env python3
"""
SOLEil Session Launcher
Ensures consistent primary agent behavior by reading context file
"""

import os
import sys
from pathlib import Path

def launch_primary_agent_session():
    """Launch a new primary agent session with consistent context"""
    
    # Read the primary agent context
    context_file = Path(__file__).parent / "PRIMARY_AGENT_CONTEXT.md"
    
    if not context_file.exists():
        print("❌ Error: PRIMARY_AGENT_CONTEXT.md not found!")
        return
    
    with open(context_file, 'r') as f:
        context = f.read()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Multi-Agent Development System                ║
    ║              Session Launcher                            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print("📖 Loading Primary Agent Context...")
    print("✅ Context loaded successfully!")
    print("\n🚀 Launching Primary Agent Session...")
    print("=" * 60)
    
    # Display the context for the AI to read
    print("PRIMARY AGENT CONTEXT:")
    print("=" * 60)
    print(context)
    print("=" * 60)
    
    print("\n🎯 Primary Agent is now ready with consistent context!")
    print("💡 The AI will now behave according to these guidelines")
    print("🤝 Murray has full control and visibility over all decisions")
    
    return context

if __name__ == "__main__":
    context = launch_primary_agent_session()
