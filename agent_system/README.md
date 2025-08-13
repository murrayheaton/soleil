# Claude-Compatible Agent System

## Overview
This is a reconfigured agent system designed to work seamlessly with Claude's built-in Task tool for delegating work to specialized agents.

## Key Features
- **Simple Integration**: Works directly with Claude's Task tool
- **PRP Processing**: Automatically analyzes PRPs and creates specialized tasks
- **Transparent Operation**: Clear visibility into what each agent is doing
- **Modular Design**: Each agent focuses on its specialty

## How Claude Uses This System

### 1. Processing a PRP
```python
# Claude can use this to analyze a PRP
from agent_system.claude_agent_system import ClaudeAgentSystem

system = ClaudeAgentSystem()
tasks = system.analyze_prp(Path("PRPs/active/PRP_12_fix_google_drive.md"))

# Then use the Task tool to delegate each task
for task in tasks:
    prompt = task.to_prompt()
    # Claude uses Task tool with prompt
```

### 2. Agent Types Available
- **Backend Agent**: API endpoints, services, business logic
- **Frontend Agent**: React components, UI, user experience  
- **Database Agent**: Schema design, migrations, optimization
- **Testing Agent**: Unit, integration, E2E tests
- **Security Agent**: Security analysis and fixes
- **Documentation Agent**: Docs, guides, comments
- **DevOps Agent**: Deployment, CI/CD, monitoring
- **Planning Agent**: Task breakdown and strategy

### 3. Task Delegation Flow
1. Claude reads the PRP or user request
2. Uses this system to create specialized tasks
3. Delegates each task using the Task tool with `subagent_type="general-purpose"`
4. Each agent works within its specialized context
5. Results are collected and integrated

## Example Usage by Claude

When you ask Claude to implement a PRP:

```
User: "Can you implement PRP_12 to fix the Google Drive integration?"

Claude:
1. Analyzes the PRP using this system
2. Creates tasks for Backend and Frontend agents
3. Uses Task tool to delegate:
   - Backend task: Implement chart service and API endpoints
   - Frontend task: Fix API calls in ChartViewer component
4. Monitors progress and reports back
5. Integrates all changes
```

## Benefits Over Previous System
- **Simpler**: No complex orchestration or queues
- **Native Integration**: Uses Claude's built-in capabilities
- **Transparent**: You see exactly what's happening
- **Efficient**: Parallel task execution when possible
- **Maintainable**: Easy to understand and modify

## Files Structure
```
agent_system/
├── claude_agent_system.py  # Main system implementation
├── README.md               # This file
├── reports/               # Task completion reports
└── contexts/             # Agent-specific contexts (if needed)
```

## Quick Commands

### Analyze Active PRPs
```bash
python agent_system/claude_agent_system.py
```

### Check Task Status
```bash
ls agent_system/reports/
```

## Integration with Claude

Claude can now:
1. Use the `ClaudeAgentSystem` class to analyze PRPs
2. Delegate specialized tasks using the Task tool
3. Track progress through the reporting system
4. Maintain full transparency with you

This system is designed to augment Claude's capabilities, not replace them. Claude remains in control and maintains transparency throughout the process.