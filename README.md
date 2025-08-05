# Soleil - Band Management Platform

A modern web application that serves as a curated wrapper around Google Workspace, designed to make band management effortless for both administrators and musicians.

## 🎵 Overview

Soleil provides role-based access to charts, audio references, setlists, and gig information, with intelligent filtering based on instrument types. Musicians get a premium, simple interface while administrators manage everything through familiar Google tools.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Google Cloud Platform account (for Google Workspace APIs)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/soleil.git
cd soleil

# Backend setup
cd band-platform/backend
python -m venv venv_linux
source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration

# Frontend setup
cd ../frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration

# Run with Docker Compose (from project root)
docker-compose up
```

## 🏗️ Architecture

### Modular Architecture
The platform uses a modular architecture designed for scalability and multi-agent development:

- **Auth Module (v1.0.0)**: Google OAuth, JWT tokens, session management
- **Content Module (v1.0.0)**: File parsing, metadata extraction, instrument filtering
- **Drive Module (v1.0.0)**: Google Drive integration, file streaming, caching
- **Sync Module (v1.0.0)**: Real-time WebSocket updates, event broadcasting
- **Dashboard Module (v1.0.0)**: Customizable UI components, user preferences
- **Core Module (v1.0.0)**: Event bus, API gateway, shared infrastructure

### Technology Stack
- **Backend**: FastAPI (Python) with async support
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL with SQLAlchemy ORM
- **File Storage**: Google Drive integration
- **Authentication**: JWT tokens with Google OAuth
- **Real-time**: WebSocket support for live updates

See [MODULES.md](MODULES.md) for detailed module documentation.

## 📁 Project Structure

```
soleil/
├── band-platform/
│   ├── backend/          # FastAPI application
│   └── frontend/         # Next.js application
├── PRPs/                 # Product Requirements Prompts
├── examples/             # Code examples and patterns
├── .claude/              # AI assistant configuration
├── CLAUDE.md            # AI assistant rules
├── DEV_LOG.md           # Human-friendly development log
├── DEV_LOG_TECHNICAL.md # Technical implementation log
└── PRODUCT_VISION.md    # Product description
```

## 🛠️ Development Workflow

This project uses Context Engineering methodology for AI-assisted development:

1. **Feature Planning**: Create an INITIAL.md file describing the feature
2. **PRP Generation**: Use `/generate-prp INITIAL.md` to create a comprehensive plan
3. **Implementation**: Use `/execute-prp PRPs/your-feature.md` to implement
4. **Documentation**: Updates to DEV_LOG.md and DEV_LOG_TECHNICAL.md are required

## 📝 Documentation

- `DEV_LOG.md` - Human-friendly progress updates
- `DEV_LOG_TECHNICAL.md` - Technical implementation details
- `PRODUCT_VISION.md` - Current product vision and features

## 🤝 Contributing

Please read `CLAUDE.md` for our development guidelines and Context Engineering workflow.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built using the Context Engineering methodology and template by Cole Medin.
