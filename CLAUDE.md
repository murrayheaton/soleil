# Claude AI Assistant Rules for SOLEil

**Last Updated:** 2025-08-05  
**Project Status:** Production-ready band platform with modular architecture and multi-agent development system

## 🎯 **Current Project State**

SOLEil is a **production-ready band platform** with:
- ✅ **Complete authentication system** (Google OAuth, JWT, sessions)
- ✅ **Professional UI** (Next.js 15, TypeScript, Tailwind CSS)
- ✅ **Google Drive integration** (file streaming, instrument-based filtering)
- ✅ **Modular backend architecture** (FastAPI, SQLAlchemy, Redis)
- ✅ **Multi-agent development system** for parallel development

## 🏗️ **Codebase Structure**

### **Root Directory** (`/soleil/`)
```
soleil/
├── band-platform/           # Main application
├── agent_system/           # Multi-agent framework
├── agent_deployment/       # Agent coordination system
├── agent_contexts/         # Agent documentation and contexts
├── PRPs/                   # Project Requirement Prompts
├── docs/                   # Project documentation
└── [various .md files]     # Project context and guides
```

### **Main Application** (`/band-platform/`)
```
band-platform/
├── backend/                # FastAPI backend
│   ├── modules/           # Modular architecture
│   │   ├── auth/         # Authentication module
│   │   ├── content/      # Content management
│   │   ├── drive/        # Google Drive integration
│   │   ├── sync/         # Real-time synchronization
│   │   ├── dashboard/    # Dashboard aggregation
│   │   └── core/         # Shared utilities
│   ├── start_server.py   # Main application entry point
│   └── requirements.txt  # Python dependencies
└── frontend/              # Next.js frontend
    ├── src/
    │   ├── app/          # Next.js app router
    │   ├── components/   # React components
    │   ├── modules/      # Frontend module components
    │   └── types/        # TypeScript definitions
    └── package.json      # Node.js dependencies
```

## 🚀 **Development Workflow**

### **1. Multi-Agent Development System**
- **NEVER work outside your assigned module** (see `AGENT_GUIDE.md`)
- **Use EventBus for cross-module communication** (see `MULTI_AGENT_DEVELOPMENT_SYSTEM.md`)
- **Follow module structure** with `MODULE.md` documentation
- **Validate modules** before committing: `python scripts/validate_module.py [module_name]`

### **2. PRP (Project Requirement Prompt) Execution**
- **Check active PRPs**: `ls PRPs/active/`
- **Read PRP completely** before starting
- **Follow module boundaries** strictly
- **Archive completed PRPs**: `mv PRPs/active/[name].md PRPs/archive/`

### **3. Code Quality Standards**
- **File size limit**: Never exceed 500 lines per file
- **Testing**: Always write tests for new functionality
- **Documentation**: Update `MODULE.md` when adding features
- **Type safety**: Use TypeScript (frontend) and type hints (Python)

## 🛠️ **Technology Stack**

### **Backend** (`/band-platform/backend/`)
- **Framework**: FastAPI with modular routing
- **Database**: SQLAlchemy with async support
- **Authentication**: Google OAuth2, JWT, session management
- **APIs**: Google Drive, Google Sheets integration
- **Testing**: Pytest with async support
- **Code Quality**: Black, Ruff, MyPy

### **Frontend** (`/band-platform/frontend/`)
- **Framework**: Next.js 15 with app router
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **State Management**: React Context + hooks
- **Testing**: Jest + React Testing Library
- **PWA**: Next-PWA for offline functionality

### **Development Tools**
- **Package Manager**: npm (frontend), pip (backend)
- **Environment**: Python 3.11+, Node.js 18+
- **Virtual Environment**: `venv_linux` (backend)
- **Code Formatting**: Black (Python), Prettier (TypeScript)

## 📋 **Development Rules**

### **✅ ALWAYS DO THIS**
1. **Read `AGENT_GUIDE.md`** before starting work
2. **Use modular architecture** - work within assigned modules only
3. **Write tests** for new functionality
4. **Update `MODULE.md`** when adding features
5. **Use EventBus** for cross-module communication
6. **Follow file size limits** (500 lines max)
7. **Use type hints** and proper error handling

### **🚫 NEVER DO THIS**
1. **NEVER modify files outside your assigned module**
2. **NEVER create direct dependencies between modules**
3. **NEVER access another module's database tables directly**
4. **NEVER import private functions** (those starting with `_`)
5. **NEVER commit without running module validation**
6. **NEVER exceed 500 lines per file**

## 🔧 **Common Commands**

### **Backend Development**
```bash
# Activate virtual environment
source band-platform/backend/venv_linux/bin/activate

# Start development server
cd band-platform/backend
python start_server.py

# Run tests
pytest

# Validate module
python scripts/validate_module.py [module_name]
```

### **Frontend Development**
```bash
# Install dependencies
cd band-platform/frontend
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### **Module Management**
```bash
# Generate module context
python scripts/generate_module_context.py [module_name]

# Validate module structure
python scripts/validate_module.py [module_name]

# Check module dependencies
python scripts/check_module_dependencies.py [module_name]
```

## 📚 **Key Documentation Files**

- **`SOLEIL_CONTEXT.md`** - Product vision and current status
- **`ARCHITECTURE.md`** - Technical architecture and module structure
- **`AGENT_GUIDE.md`** - AI agent development guidelines
- **`MULTI_AGENT_DEVELOPMENT_SYSTEM.md`** - Agent system architecture
- **`TASK.md`** - Current development tasks and progress
- **`PRPs/active/`** - Active project requirements

## 🌐 **Environment & Deployment**

### **Production**
- **Domain**: https://solepower.live
- **API**: https://solepower.live/api
- **Environment**: Production Docker containers

### **Development**
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Environment**: Local development with `.env` files

## 🧪 **Testing Strategy**

### **Backend Testing**
- **Unit tests**: Module-specific test suites
- **Integration tests**: Cross-module functionality
- **API tests**: Endpoint validation
- **Database tests**: Model and migration testing

### **Frontend Testing**
- **Component tests**: Individual React components
- **Integration tests**: User workflows
- **E2E tests**: Complete user journeys
- **Accessibility tests**: Screen reader and keyboard navigation

## 📝 **Documentation Requirements**

### **Module Documentation**
- **`MODULE.md`**: Primary module documentation
- **Function docstrings**: Google style with type hints
- **Inline comments**: Explain complex logic with `# Reason:` comments
- **API documentation**: OpenAPI/Swagger specs

### **Project Documentation**
- **Update frequency**: After every 15 user prompts OR when implementation is complete
- **Chronological format**: Dated entries with user prompt references
- **Version control**: Create dated versions for major milestones

## 🔍 **Debugging & Troubleshooting**

### **Common Issues**
- **Module import errors**: Check `__init__.py` files and module registration
- **Circular dependencies**: Use EventBus for cross-module communication
- **Type errors**: Ensure proper type hints and TypeScript configuration
- **Authentication issues**: Check OAuth credentials and session configuration

### **Debug Tools**
- **Backend logging**: Check `backend.log` and `server.log`
- **Frontend logging**: Check browser console and `frontend.log`
- **Module validation**: Use `validate_module.py` script
- **Dependency checking**: Use `check_module_dependencies.py` script

## 🎯 **Current Development Focus**

- **Offline chart viewer** (PRP 10)
- **Google Drive chart integration fixes** (PRP 12)
- **Frontend quality improvements** (PRP frontend_quality_check)
- **Multi-agent system optimization**

---

**Remember**: SOLEil is a production-ready platform. Always maintain code quality, follow the modular architecture, and work within your assigned module boundaries. When in doubt, refer to the module's `MODULE.md` file and the `AGENT_GUIDE.md` for guidance.
