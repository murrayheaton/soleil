#!/usr/bin/env python3
"""
Start the SOLEil Multi-Agent Development System
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from modules.core.agent_coordinator import AgentCoordinator, AgentType
from modules.core.event_bus import EventBus
from modules.core.api_gateway import APIGateway
from modules.core.agent_handoff_system import HandoffManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_multi_agent_system():
    """Start the multi-agent development system."""
    logger.info("🚀 Starting SOLEil Multi-Agent Development System...")
    
    try:
        # Initialize core components
        logger.info("📡 Initializing Event Bus...")
        event_bus = EventBus()
        
        logger.info("🌐 Initializing API Gateway...")
        api_gateway = APIGateway()
        
        logger.info("👥 Initializing Agent Coordinator...")
        agent_coordinator = AgentCoordinator(event_bus, api_gateway)
        
        logger.info("🤝 Initializing Handoff Manager...")
        handoff_manager = HandoffManager(event_bus, agent_coordinator)
        
        # Register default agents
        logger.info("🔧 Registering default agents...")
        
        # Register Orchestrator Agent
        await agent_coordinator.register_agent(
            agent_id="orchestrator_001",
            agent_type=AgentType.INTEGRATION,  # Use integration type for orchestrator
            custom_permissions={
                "/": {"read", "write", "execute", "approve"}
            }
        )
        
        # Register Frontend Agent
        await agent_coordinator.register_agent(
            agent_id="frontend_001",
            agent_type=AgentType.INTEGRATION,  # Use integration type for frontend
            custom_permissions={
                "/band-platform/frontend/": {"read", "write", "execute"},
                "/agent_contexts/soleil_agents/frontend_agent.md": {"read"}
            }
        )
        
        # Register Backend Agent
        await agent_coordinator.register_agent(
            agent_id="backend_001",
            agent_type=AgentType.INTEGRATION,  # Use integration type for backend
            custom_permissions={
                "/band-platform/backend/": {"read", "write", "execute"},
                "/agent_contexts/soleil_agents/backend_agent.md": {"read"}
            }
        )
        
        # Register Testing Agent
        await agent_coordinator.register_agent(
            agent_id="testing_001",
            agent_type=AgentType.INTEGRATION,  # Use integration type for testing
            custom_permissions={
                "/tests/": {"read", "write", "execute"},
                "/agent_contexts/soleil_agents/unit_test_agent.md": {"read"}
            }
        )
        
        # Register Security Agent
        await agent_coordinator.register_agent(
            agent_id="security_001",
            agent_type=AgentType.INTEGRATION,  # Use integration type for security
            custom_permissions={
                "/": {"read", "write", "execute", "approve"}
            }
        )
        
        logger.info("✅ Multi-agent system started successfully!")
        logger.info(f"📊 Active agents: {len(agent_coordinator.agents)}")
        
        # List registered agents
        active_agents = await agent_coordinator.get_active_agents()
        for agent in active_agents:
            logger.info(f"  - {agent['agent_id']} ({agent['agent_type']}) - {agent['status']}")
        
        # Start event loop
        logger.info("🔄 Multi-agent system is running. Press Ctrl+C to stop.")
        
        # Keep the system running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Failed to start multi-agent system: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(start_multi_agent_system())
    except KeyboardInterrupt:
        logger.info("🛑 Multi-agent system stopped by user")
    except Exception as e:
        logger.error(f"💥 Multi-agent system crashed: {e}")
        sys.exit(1)
