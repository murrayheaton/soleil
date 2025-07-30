# Contributing to Soleil

Thank you for your interest in contributing to Soleil! This project uses Context Engineering methodology to ensure high-quality, AI-assisted development.

## 🎯 Context Engineering Workflow

### Understanding the Approach

Context Engineering is about providing comprehensive context to AI coding assistants, enabling them to implement features correctly on the first try. It's 10x more effective than prompt engineering.

### Key Files

1. **CLAUDE.md** - Global rules and conventions that apply to every coding session
2. **INITIAL_*.md** - Feature request templates describing what to build
3. **PRPs/** - Product Requirements Prompts containing implementation blueprints
4. **DEV_LOG.md** - Human-readable progress updates
5. **DEV_LOG_TECHNICAL.md** - Technical implementation details

## 🚀 How to Contribute

### 1. Check Current Tasks

Before starting work, check `TASK.md` to see what's being worked on and add your intended task.

### 2. For New Features

1. Create an INITIAL file describing your feature:
   ```bash
   cp INITIAL_soleil.md INITIAL_your_feature.md
   ```

2. Edit the file with:
   - Clear description of the feature
   - Examples to follow
   - Relevant documentation
   - Important considerations

3. Generate a PRP using Claude Code:
   ```bash
   /generate-prp INITIAL_your_feature.md
   ```

4. Review the generated PRP in `PRPs/active/`

5. Execute the implementation:
   ```bash
   /execute-prp PRPs/active/your-feature.md
   ```

### 3. For Bug Fixes

1. Create a failing test that demonstrates the bug
2. Fix the bug
3. Ensure all tests pass
4. Update both DEV_LOG files

### 4. Code Style

- **Python**: Follow PEP8, use type hints, format with `black`
- **TypeScript**: Use ESLint configuration, prefer functional components
- **Documentation**: Every function needs a docstring/JSDoc
- **Tests**: Every feature needs tests (happy path, edge case, error case)

### 5. Testing Requirements

Before submitting:

```bash
# Backend
cd band-platform/backend
source venv_linux/bin/activate
ruff check . --fix
mypy .
pytest tests/ -v

# Frontend
cd band-platform/frontend
npm run lint
npm run test
npm run build
```

### 6. Documentation Updates

After implementing features, you MUST update:

1. **DEV_LOG.md** - Add a human-friendly summary
2. **DEV_LOG_TECHNICAL.md** - Add technical details
3. **README.md** - If you added dependencies or setup steps
4. **PRODUCT_VISION.md** - If you added user-facing features

## 📝 Commit Messages

Use the template in `.gitmessage`:

```
feat: add Google Drive sync engine

Implement background worker that monitors Drive for changes
and updates local database. Includes rate limiting and
error recovery.

Closes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🏗️ Architecture Guidelines

### Backend (FastAPI)
- Keep endpoints focused and RESTful
- Use dependency injection for services
- Implement proper error handling
- Add OpenAPI documentation

### Frontend (Next.js)
- Mobile-first responsive design
- Optimize for offline functionality
- Use React Query for data fetching
- Implement proper loading states

### Database
- Always create migrations for schema changes
- Use indexes for frequently queried fields
- Design for multi-tenancy from the start

## 🔍 Code Review Process

1. All code must pass automated tests
2. Follow existing patterns in the codebase
3. Include tests for new functionality
4. Update documentation as needed
5. Respond to review feedback constructively

## 🤝 Community

- Be respectful and constructive
- Help others learn Context Engineering
- Share your implementation experiences
- Suggest improvements to the workflow

## ❓ Questions?

If you're unsure about anything:
1. Check existing PRPs for patterns
2. Review the codebase for examples
3. Ask in discussions/issues
4. When in doubt, over-document

Remember: The goal is to make it easy for AI assistants (and humans) to understand and extend the codebase!
