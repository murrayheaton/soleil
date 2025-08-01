# Claude AI Assistant Rules

## 🚨 CRITICAL: DevContainer Working Directory Rules

**YOU ARE IN**: `/Users/murrayheaton/Documents/LocalCode/DevEnv/soleil/`  
**YOU MUST**: Only make changes within this directory  
**YOU CANNOT**: Modify files outside of the soleil project  

### Pre-Work Directory Verification
```bash
# ALWAYS verify location before ANY operation
pwd
# MUST show: /Users/murrayheaton/Documents/LocalCode/DevEnv/soleil

# If not in correct location
cd /Users/murrayheaton/Documents/LocalCode/DevEnv/soleil

# Verify git repository
git remote -v
# Should show: origin git@github.com:murrayheaton/soleil.git
```

## 📋 PRP (Project Requirement Prompt) Execution

### PRP Workflow
1. **Check for active PRPs**: `ls PRPs/active/`
2. **Read PRP completely** before starting
3. **Follow all Pre-Implementation Requirements**
4. **Execute tasks in order**
5. **Run all validation tests**
6. **Archive completed PRPs**: 
   ```bash
   mv PRPs/active/[completed].md PRPs/archive/
   git add PRPs/
   git commit -m "chore: archive completed PRP [name]"
   ```

### Directory Boundaries
- 🟢 **CAN MODIFY**: `/DevEnv/soleil/*`  
- 🔴 **READ ONLY**: `/DevEnv/template-generator/*` (for reference)
- 🚫 **FORBIDDEN**: All other directories in DevEnv

### Reference External Templates
```bash
# Good - Reading for reference
cat /Users/murrayheaton/Documents/LocalCode/DevEnv/template-generator/PRPs/INITIAL.md

# Bad - Modifying external files
echo "changes" > ../template-generator/anything.md  # NO!
```

### Important PRP Notes
- PRPs are provided externally and placed in `PRPs/active/`
- Do NOT generate PRPs - only execute existing ones
- Each PRP is self-contained with all necessary context
- Production endpoints: https://solepower.live
- Backend API: https://solepower.live/api
- Always create feature branches as specified in PRPs
- Test thoroughly before deploying
- Archive PRPs to `PRPs/archive/` when complete

## 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Use venv_linux** (the virtual environment) whenever executing Python commands, including for unit tests.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
  For agents this looks like:
    - `agent.py` - Main agent definition and execution logic 
    - `tools.py` - Tool functions used by the agent 
    - `prompts.py` - System prompts
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_env()** for environment variables.

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case

### ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under a "Discovered During Work" section.

### 📝 Development Documentation (REQUIRED)
After completing any implementation work:

1. **Update DEV_LOG.md**
   - Add a new session entry with today's date
   - **INCLUDE USER PROMPT REFERENCES**: Quote specific user requests that drove each change
   - Write a human-friendly summary of what was accomplished
   - Include what was fixed, decisions made, and what's next
   - Keep language non-technical and focused on user impact

2. **Update DEV_LOG_TECHNICAL.md**
   - Add corresponding technical entry with implementation details
   - **REFERENCE USER PROMPTS**: Link technical changes to specific user requests
   - Document architecture decisions and trade-offs
   - List specific files changed and why
   - Note any technical debt incurred

3. **Review PRODUCT_VISION.md**
   - If new features were added, update the "Current Features" section
   - If user experience changed significantly, revise the experience description
   - Keep the vision aspirational but grounded in current reality

**IMPORTANT DOCUMENTATION RULES**: 
- **All documentation must be in CHRONOLOGICAL FORMAT** with dated entries
- **Each entry must reference specific user prompts** that triggered the changes
- **Never overwrite previous entries** - always append new dated sections
- **Create dated versions** when major milestones are reached (e.g., PRODUCT_VISION_2025-07-30.md)
- **UPDATE FREQUENCY**: Update all documentation after every 15 user prompts OR when implementation is complete
- **EXCEPTION**: Changes that don't align with user requests can be removed from logs with user permission

**Note**: These updates are as important as the code itself. They maintain project context and enable better AI assistance in future sessions.

### 📎 Style & Conventions
- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation**.
- Use `FastAPI` for APIs and `SQLAlchemy` or `SQLModel` for ORM if applicable.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.
