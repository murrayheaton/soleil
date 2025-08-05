# PRP: Create Agent Assignment System

## Overview
Implement a system for assigning and managing AI agents to specific modules, including agent contexts, permissions, and coordination mechanisms.

## Context
- This PRP should be implemented after the modular architecture is complete
- Enables true multi-agent development with clear boundaries
- Each agent will have a specific module assignment and context
- Reference: MODULAR_ARCHITECTURE_PROPOSAL.md

## Pre-Implementation Requirements
1. Complete PRP 08 (Module Integration and Cleanup)
2. All modules must have complete MODULE.md files
3. Create new branch: `feature/agent-assignment-system`
4. Review existing CLAUDE.md for patterns

## Implementation Tasks

### 1. Create Agent Context System
- [ ] Create `agent_contexts/` directory in project root
- [ ] Create `agent_contexts/AGENT_TEMPLATE.md`:
  ```markdown
  # Agent: [Module Name] Specialist
  
  ## Your Identity
  You are an AI agent specialized in the [Module] module of SOLEil.
  
  ## Your Scope
  - Primary responsibility: /band-platform/backend/modules/[module]/
  - Frontend responsibility: /band-platform/frontend/src/modules/[module]/
  - You own all code within these directories
  
  ## Your Capabilities
  - Read and modify files within your module
  - Create tests for your module
  - Update your MODULE.md documentation
  - Communicate with other modules via EventBus
  
  ## Your Restrictions
  - Cannot modify files outside your module directories
  - Cannot change module interfaces without coordination
  - Must maintain backward compatibility
  - Must update tests when changing code
  
  ## Key Files
  [List of important files in the module]
  
  ## Module Dependencies
  [List of other modules this depends on]
  
  ## Before Making Changes
  1. Read your MODULE.md
  2. Check module health status
  3. Run module-specific tests
  4. Consider impact on dependent modules
  ```

### 2. Create Agent-Specific Contexts
- [ ] Create `agent_contexts/auth_agent.md`
- [ ] Create `agent_contexts/content_agent.md`
- [ ] Create `agent_contexts/drive_agent.md`
- [ ] Create `agent_contexts/sync_agent.md`
- [ ] Create `agent_contexts/dashboard_agent.md`
- [ ] Create `agent_contexts/integration_agent.md` (for cross-module work)

### 3. Implement Agent Coordination System
- [ ] Create `modules/core/agent_coordinator.py`:
  ```python
  class AgentCoordinator:
      def register_agent(self, agent_id: str, module: str)
      def request_cross_module_change(self, from_agent: str, to_module: str, change: dict)
      def get_module_owner(self, file_path: str) -> str
      def validate_agent_permissions(self, agent_id: str, file_path: str) -> bool
  ```
- [ ] Create coordination rules and protocols
- [ ] Implement change request queue system

### 4. Create Agent Communication Protocol
- [ ] Create `agent_contexts/COMMUNICATION_PROTOCOL.md`:
  - [ ] How agents request cross-module changes
  - [ ] How agents coordinate on shared interfaces
  - [ ] Conflict resolution procedures
  - [ ] Emergency override procedures
- [ ] Define standard message formats
- [ ] Create examples of agent interactions

### 5. Implement Agent Workspace Isolation
- [ ] Create `scripts/create_agent_workspace.py`:
  - [ ] Set up isolated workspace for an agent
  - [ ] Include only relevant module files
  - [ ] Generate focused context
- [ ] Create `scripts/sync_agent_changes.py`:
  - [ ] Sync changes from agent workspace
  - [ ] Validate changes stay within bounds
  - [ ] Run affected tests

### 6. Create Agent Performance Tracking
- [ ] Add agent tracking to modules:
  - [ ] Track which agent made changes
  - [ ] Log agent decisions and rationale
  - [ ] Monitor agent performance metrics
- [ ] Create `agent_metrics/` directory
- [ ] Implement agent scoreboard

### 7. Develop Agent Handoff System
- [ ] Create `agent_contexts/HANDOFF_PROTOCOL.md`
- [ ] Implement handoff tracking:
  - [ ] Current agent assignments
  - [ ] Work in progress
  - [ ] Blocked tasks
  - [ ] Handoff notes
- [ ] Create handoff templates

### 8. Create Multi-Agent Testing Framework
- [ ] Implement `tests/multi_agent/` directory
- [ ] Create tests for agent boundaries:
  - [ ] Test permission enforcement
  - [ ] Test cross-module communication
  - [ ] Test conflict scenarios
- [ ] Add agent simulation tests

### 9. Build Agent Dashboard
- [ ] Create `/api/agents` endpoint:
  - [ ] List active agents
  - [ ] Show agent assignments
  - [ ] Display agent metrics
  - [ ] Show coordination requests
- [ ] Create simple UI for agent monitoring
- [ ] Add WebSocket updates for real-time tracking

### 10. Create Agent Onboarding System
- [ ] Create `scripts/onboard_new_agent.py`:
  - [ ] Generate agent-specific context
  - [ ] Set up permissions
  - [ ] Create initial tasks
  - [ ] Run orientation tests
- [ ] Create `agent_contexts/ONBOARDING.md`
- [ ] Implement buddy system for new agents

## Validation Steps
1. Test agent isolation:
   - [ ] Attempt cross-module changes (should fail)
   - [ ] Test permission validation
2. Test agent coordination:
   - [ ] Submit cross-module request
   - [ ] Test approval workflow
3. Test with multiple simulated agents
4. Verify metrics collection works

## Success Criteria
- [ ] Agents can work independently on modules
- [ ] Agent boundaries are enforced
- [ ] Cross-module coordination works smoothly
- [ ] Agent metrics are tracked
- [ ] Handoff process is clear
- [ ] New agents can be onboarded easily

## Example Agent Assignment
```
Auth Agent: Handles all authentication
- Google OAuth
- Session management  
- User profiles

Content Agent: Manages content parsing
- File organization
- Instrument filtering
- Metadata extraction

Integration Agent: Handles cross-cutting concerns
- API gateway updates
- Event bus modifications
- Integration tests
```

## Post-Implementation
1. Run multi-agent simulation tests
2. Document agent best practices
3. Create agent assignment schedule
4. Update CLAUDE.md with agent system
5. Begin pilot with 2-3 agents
6. Monitor and refine system