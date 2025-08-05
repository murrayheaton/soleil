# SOLEil Band Platform - Project Planning

## 🎯 Project Overview

SOLEil (Sole Power Live) is a band platform designed to help musicians collaborate, manage their creative process, and build their careers. The project uses Context Engineering methodology to ensure high-quality, AI-assisted development.

**Current Status**: Production-ready platform with complete authentication, file management, and professional UI.

## 🏗️ Architecture

### Modular Architecture (Completed)
The platform has been successfully migrated to a modular architecture that enables multi-agent development and better scalability.

**Core Modules**:
- **Auth Module (v1.0.0)**: Google OAuth, JWT, session management, user profiles
- **Content Module (v1.0.0)**: File parsing, instrument filtering, chart metadata
- **Drive Module (v1.0.0)**: Google Drive integration, file streaming, caching
- **Sync Module (v1.0.0)**: WebSocket real-time updates, event broadcasting
- **Dashboard Module (v1.0.0)**: UI components, module grid system
- **Core Module (v1.0.0)**: EventBus, API Gateway, shared infrastructure

See MODULES.md for detailed module documentation and AGENT_GUIDE.md for AI agent development guidelines.

### Backend
- **Framework**: FastAPI with modular routing
- **Database**: SQLAlchemy/SQLModel for ORM
- **Environment**: Python with venv_linux virtual environment
- **Testing**: Pytest with module-specific test suites
- **Code Quality**: Black formatter, Ruff linter, MyPy type checking
- **Architecture**: Service layer pattern with clear module boundaries

### Frontend
- **Framework**: Next.js with module-based component organization
- **Design**: Mobile-first responsive design
- **Data Fetching**: React Query with module-specific hooks
- **Testing**: Jest/React Testing Library
- **Build**: npm run build
- **State Management**: Module-scoped contexts and hooks

### Development Philosophy
- **File Size Limit**: Never exceed 500 lines per file
- **Modularity**: Self-contained modules with MODULE.md documentation
- **Testing**: Module-specific test suites (unit, integration, e2e)
- **Documentation**: MODULE.md for each module + function docstrings
- **Communication**: Event bus for loose coupling between modules

## 📁 Project Structure

### Current Structure (Production)
```
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── venv_linux/          # Virtual environment
│   │   ├── start_server.py      # Main FastAPI application
│   │   ├── app/                 # Application code
│   │   │   ├── services/        # Business logic services
│   │   │   ├── models/          # Database models
│   │   │   └── utils/           # Utilities and helpers
│   │   └── user_profiles.json   # User profile persistence
│   └── frontend/
│       └── src/
│           ├── app/             # Next.js pages
│           ├── components/      # React components
│           ├── lib/             # API clients and utilities
│           └── types/           # TypeScript definitions
├── PRPs/                        # Project Requirement Prompts
│   ├── active/                  # PRPs ready for execution
│   └── archive/                 # Completed PRPs
├── MODULAR_ARCHITECTURE_PROPOSAL.md  # Migration plan
└── [documentation files]        # Various .md files
```

### Current Modular Structure
```
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── modules/
│   │   │   ├── auth/           # Authentication module
│   │   │   ├── content/        # Content management module
│   │   │   ├── drive/          # Google Drive module
│   │   │   ├── sync/           # Synchronization module
│   │   │   └── dashboard/      # Dashboard aggregation
│   │   ├── core/               # Shared utilities and config
│   │   └── start_server.py     # Module registration and startup
│   └── frontend/
│       └── src/
│           ├── modules/         # Frontend module components
│           └── core/            # Shared components and utilities
└── [documentation files]
```

## 🧱 Code Organization Patterns

### Module Structure
Each module follows this pattern:
```
module_name/
├── MODULE.md           # Module documentation and context
├── __init__.py         # Public module interface
├── api/                # FastAPI route handlers
├── services/           # Business logic
├── models/             # Data models
├── types/              # TypeScript types (frontend modules)
├── tests/              # Module-specific tests
└── frontend/           # Frontend components (if applicable)
    ├── components/
    ├── hooks/
    └── utils/
```

### Module Communication
- **Direct Import**: Only from module's public interface (`__init__.py`)
- **Event Bus**: For loose coupling between modules
- **API Gateway**: Central routing and service discovery
- **Dependency Injection**: For testing and flexibility

### General Principles
- Each module must have a MODULE.md file
- Use relative imports within modules
- Use python_dotenv and load_env() for environment variables
- Follow PEP8 with type hints
- Use Pydantic for data validation
- Module interfaces must be explicitly defined

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