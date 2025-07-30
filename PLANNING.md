# SOLEil Band Platform - Project Planning

## 🎯 Project Overview

SOLEil (Sole Power Live) is a band platform designed to help musicians collaborate, manage their creative process, and build their careers. The project uses Context Engineering methodology to ensure high-quality, AI-assisted development.

**Current Status**: Production-ready platform with complete authentication, file management, and professional UI.

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI
- **Database**: SQLAlchemy/SQLModel for ORM
- **Environment**: Python with venv_linux virtual environment
- **Testing**: Pytest
- **Code Quality**: Black formatter, Ruff linter, MyPy type checking

### Frontend
- **Framework**: Next.js
- **Design**: Mobile-first responsive design
- **Data Fetching**: React Query
- **Testing**: Jest/React Testing Library
- **Build**: npm run build

### Development Philosophy
- **File Size Limit**: Never exceed 500 lines per file
- **Modularity**: Organize code into clear feature-based modules
- **Testing**: Every feature needs unit tests (happy path, edge case, error case)
- **Documentation**: Every function needs docstrings using Google style

## 📁 Project Structure

```
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── venv_linux/          # Virtual environment
│   │   ├── start_server.py      # Main FastAPI application (PRODUCTION READY)
│   │   ├── google_token.json    # OAuth2 token storage
│   │   └── user_profiles.json   # User profile persistence
│   └── frontend/
│       └── src/
│           ├── app/
│           │   ├── page.tsx               # Profile landing page (PRODUCTION READY)
│           │   └── repertoire/page.tsx    # File browser interface (PRODUCTION READY)
│           └── components/
│               └── Layout.tsx             # Navigation component (PRODUCTION READY)
├── start_sole_power_live.sh     # Production launcher script
├── CLAUDE.md                    # Global AI assistant rules
├── TASK.md                      # Current task tracking
├── DEV_LOG.md                   # Human-readable progress
├── DEV_LOG_TECHNICAL.md         # Technical implementation details
└── PRODUCT_VISION.md            # Product vision and features
```

## 🧱 Code Organization Patterns

### For Agents/Services
- `agent.py` - Main agent definition and execution logic
- `tools.py` - Tool functions used by the agent
- `prompts.py` - System prompts

### General Principles
- Use relative imports within packages
- Use python_dotenv and load_env() for environment variables
- Follow PEP8 with type hints
- Use Pydantic for data validation

## 🧪 Testing Strategy

- **Location**: Tests mirror main app structure in `/tests` folder
- **Framework**: Pytest for backend, Jest for frontend
- **Coverage**: Minimum 3 tests per feature:
  1. Expected use case
  2. Edge case
  3. Failure case

## 📝 Documentation Requirements

Every implementation must update:
1. **DEV_LOG.md** - Human-friendly summary
2. **DEV_LOG_TECHNICAL.md** - Technical details
3. **README.md** - If dependencies or setup changed
4. **PRODUCT_VISION.md** - If user-facing features added

## 🔄 Development Workflow

1. Check `TASK.md` before starting work
2. Add new tasks with today's date
3. Create tests first (TDD approach)
4. Implement feature following architecture patterns
5. Run quality checks (ruff, mypy, tests)
6. Update documentation
7. Mark tasks complete in `TASK.md`

## 🎨 Style Guidelines

- **Python**: PEP8, Black formatting, type hints required
- **TypeScript**: ESLint configuration, functional components
- **Comments**: Use `# Reason:` for complex logic explanations
- **Imports**: Prefer relative imports within packages
- **Environment**: Always use venv_linux for Python commands

## 🚫 Constraints

- Never create files longer than 500 lines
- Never assume missing context - ask questions
- Never hallucinate libraries - only use verified packages
- Always confirm file paths exist before referencing
- Never delete existing code unless explicitly instructed