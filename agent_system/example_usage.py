#!/usr/bin/env python3
"""
Example of how Claude uses the agent system to process PRPs
"""

from pathlib import Path
from claude_agent_system import ClaudeAgentSystem, AgentType

def demonstrate_prp_processing():
    """
    This demonstrates how Claude would process PRP_12 (Fix Google Drive Chart Integration)
    """
    
    print("=== Claude Agent System Demo ===\n")
    
    # Initialize the system
    system = ClaudeAgentSystem()
    
    # Find the Google Drive PRP
    prp_path = Path("/Users/murrayheaton/Documents/GitHub/soleil/PRPs/active/PRP_12_fix_google_drive_chart_integration.md")
    
    if prp_path.exists():
        print(f"Processing: {prp_path.name}\n")
        
        # Analyze and create tasks
        tasks = system.analyze_prp(prp_path)
        
        print(f"Created {len(tasks)} specialized tasks:\n")
        
        for task in tasks:
            print(f"{'='*50}")
            print(f"Agent Type: {task.agent_type.value.upper()}")
            print(f"Task ID: {task.task_id}")
            print(f"Description: {task.description}")
            print(f"\nContext:")
            for key, value in task.context.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value[:3]:  # Show first 3 items
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")
            print()
            
            # Show how Claude would use this
            print("Claude would delegate this using:")
            print("```")
            print("Task tool with subagent_type='general-purpose'")
            print(f"Prompt: {task.description}")
            print("```")
            print()
    
    else:
        print(f"PRP not found: {prp_path}")
    
    # Show how to check all active PRPs
    print("\n" + "="*50)
    print("All Active PRPs:")
    
    prp_dir = Path("/Users/murrayheaton/Documents/GitHub/soleil/PRPs/active")
    for prp in prp_dir.glob("*.md"):
        print(f"  - {prp.name}")


def demonstrate_manual_task_creation():
    """
    This shows how Claude can manually create specific tasks
    """
    
    print("\n=== Manual Task Creation Demo ===\n")
    
    from claude_agent_system import AgentTask
    import datetime
    
    # Create a specific backend task
    backend_task = AgentTask(
        task_id=f"backend_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        agent_type=AgentType.BACKEND,
        description="Connect Google Drive service to chart API endpoints",
        context={
            "files_to_modify": [
                "/band-platform/backend/modules/content/api/content_routes.py",
                "/band-platform/backend/modules/content/services/chart_service.py"
            ],
            "requirements": [
                "Implement list_charts endpoint using GoogleDriveService",
                "Add chart download endpoint with streaming",
                "Handle Google Drive authentication",
                "Add proper error handling"
            ],
            "google_account": "murray@projectbrass.live"
        },
        priority=1
    )
    
    print("Backend Task Created:")
    print(f"  ID: {backend_task.task_id}")
    print(f"  Type: {backend_task.agent_type.value}")
    print(f"  Description: {backend_task.description}")
    
    # Show the prompt that would be sent to the Task tool
    print("\nPrompt for Task tool:")
    print("-" * 40)
    print(backend_task.to_prompt()[:500] + "...")  # Show first 500 chars
    
    # Create a frontend task
    frontend_task = AgentTask(
        task_id=f"frontend_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        agent_type=AgentType.FRONTEND,
        description="Fix ChartViewer API integration",
        context={
            "component": "/band-platform/frontend/src/components/ChartViewer.tsx",
            "api_service": "/band-platform/frontend/src/lib/api.ts",
            "requirements": [
                "Update API endpoints to match backend",
                "Add proper error handling",
                "Show loading states",
                "Handle offline mode"
            ]
        },
        priority=2
    )
    
    print("\n\nFrontend Task Created:")
    print(f"  ID: {frontend_task.task_id}")
    print(f"  Type: {frontend_task.agent_type.value}")
    print(f"  Description: {frontend_task.description}")


if __name__ == "__main__":
    # Run the demonstrations
    demonstrate_prp_processing()
    demonstrate_manual_task_creation()
    
    print("\n" + "="*50)
    print("Demo complete! Claude can now use this system to:")
    print("1. Analyze PRPs and create specialized tasks")
    print("2. Delegate tasks using the Task tool")
    print("3. Track progress and collect results")
    print("4. Maintain full transparency with the user")