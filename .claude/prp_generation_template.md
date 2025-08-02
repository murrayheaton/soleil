# PRP Generation Template for Soleil Band Platform

## TECHNOLOGY/FRAMEWORK:

**Your technology:** Soleil - A Google Workspace-integrated PWA for band/gig management using:
- **Backend**: Python (FastAPI, SQLAlchemy, Google APIs)
- **Frontend**: Next.js PWA with TypeScript, React, Tailwind CSS
- **Infrastructure**: Docker, Nginx, SSL/TLS
- **Integrations**: Google Drive, Sheets, Calendar APIs
- **Storage**: PostgreSQL + JSON file storage for profiles

---

## TEMPLATE PURPOSE:

**What specific use case should this template be optimized for?**

Creating detailed, actionable Project Requirement Prompts (PRPs) for the Soleil platform that guide developers (human or AI) through specific feature implementations, bug fixes, or system improvements. Each PRP should be self-contained with clear goals, implementation steps, testing procedures, and rollback plans.


**Your purpose:** Generate PRPs that enable systematic development of a production-ready band management platform that seamlessly integrates Google Workspace tools with a premium musician-friendly interface, supporting both administrators and musicians with role-based access to charts, setlists, audio references, and gig information.

---

## CORE FEATURES:

**What are the essential features this template should help developers implement?**

**Authentication & User Management:**
- Google OAuth 2.0 integration with proper session handling
- Profile persistence and management
- Role-based access control (Admin, Musician, Guest)
- Instrument-based content filtering

**Google Workspace Integration:**
- Drive API integration for file access and real-time sync
- Sheets API for setlist and gig database management
- Calendar API for schedule integration
- Intelligent file naming convention parsing (e.g., "Song Title - Bb.pdf")
- Background sync with error recovery

**PWA & Mobile Features:**
- Offline chart and audio storage
- Service worker implementation
- Push notifications for gig updates
- Cross-platform responsive design
- PDF viewing with zoom/pan capabilities

**Performance & Reliability:**
- Fast chart loading (<2 seconds)
- Robust error handling and logging
- Session management and recovery
- File caching and CDN integration
- Rate limiting for API calls

**Your core features:** Each PRP should address specific aspects of these features with production-ready code examples and detailed implementation steps.

---

## EXAMPLES TO INCLUDE:

**What working examples should be provided in the template?**

**PRP Structure Examples:**
- Bug fix PRPs (like `01_fix_profile_loading_issue.md`)
- Feature implementation PRPs (like `03_dashboard_implementation.md`)
- UI/UX enhancement PRPs (like `02_navigation_ui_updates.md`)
- Integration PRPs (Google Drive sync, Calendar integration)
- Performance optimization PRPs

**Code Pattern Examples:**
- Async Python service patterns with proper error handling
- React component patterns with TypeScript
- API endpoint patterns with authentication
- Google API integration patterns
- Docker deployment patterns

**Your examples:** Each PRP should include complete, working code snippets that can be directly implemented, following the project's established patterns.

---

## DOCUMENTATION TO RESEARCH:

**What specific documentation should be thoroughly researched and referenced?**

**Project Documentation:**
- CLAUDE.md - AI assistant interaction guidelines
- PLANNING.md - Architecture and technical decisions
- PRODUCT_VISION.md - Feature requirements and user stories
- DEV_LOG.md & DEV_LOG_TECHNICAL.md - Implementation history
- GOOGLE_DRIVE_SETUP.md - Google integration patterns

**External Documentation:**
- https://developers.google.com/drive/api/v3/reference - Drive API
- https://developers.google.com/sheets/api/reference/rest - Sheets API
- https://developers.google.com/calendar/api/v3/reference - Calendar API
- https://fastapi.tiangolo.com/tutorial/ - FastAPI patterns
- https://nextjs.org/docs/app/building-your-application - Next.js App Router
- https://web.dev/progressive-web-apps/ - PWA best practices

**Your documentation:** PRPs should reference both internal project docs and external API documentation as needed.

---

## DEVELOPMENT PATTERNS:

**What specific development patterns, project structures, or workflows should be researched and included?**

**Code Organization:**
```
band-platform/
├── backend/
│   ├── app/
│   │   ├── services/     # Business logic services
│   │   ├── api/          # FastAPI routes
│   │   └── models/       # SQLAlchemy models
│   └── start_server.py   # Main application
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities and API clients
│   └── public/           # Static assets
└── docker-compose.*.yml  # Deployment configs
```

**Git Workflow:**
- Feature branches: `feature/description`
- Bug fix branches: `fix/description`
- Always branch from main
- Test locally before deployment
- Update DEV_LOG files after major changes

**Your development patterns:** PRPs should enforce consistent patterns for error handling, logging, testing, and deployment.

---

## SECURITY & BEST PRACTICES:

**What security considerations and best practices are critical for this technology?**

**Authentication Security:**
- Secure session management with proper timeouts
- CSRF protection on all state-changing operations
- Secure cookie settings (httpOnly, secure, sameSite)
- OAuth state parameter validation

**API Security:**
- Rate limiting on all endpoints
- Input validation and sanitization
- Proper CORS configuration
- API key rotation for Google services

**Data Protection:**
- Encryption at rest for sensitive data
- HTTPS enforcement
- Secure file upload validation
- User data isolation

**Your security considerations:** Each PRP should include security checks relevant to the feature being implemented.

---

## COMMON GOTCHAS:

**What are the typical pitfalls, edge cases, or complex issues developers face with this technology?**

**Google API Issues:**
- Rate limit handling (exponential backoff)
- Token refresh failures
- Large file handling limitations
- Quota management across multiple users

**PWA Challenges:**
- iOS PWA limitations
- Service worker update strategies
- IndexedDB storage limits
- Offline/online sync conflicts

**Production Issues:**
- Docker volume permissions
- SSL certificate renewal
- Session persistence across deployments
- Database migration rollbacks

**Your gotchas:** PRPs should proactively address these common issues with tested solutions.

---

## VALIDATION REQUIREMENTS:

**What specific validation, testing, or quality checks should be included in the template?**

**Testing Checklist:**
- Local development testing steps
- Production deployment validation
- Cross-browser compatibility checks
- Mobile device testing (iOS/Android)
- Offline functionality verification
- Performance benchmarks

**Monitoring Requirements:**
- Error logging verification
- API response time checks
- User session tracking
- Google API quota monitoring
- Storage usage tracking

**Your validation requirements:** Each PRP must include specific test cases and validation steps.

---

## INTEGRATION FOCUS:

**What specific integrations or third-party services are commonly used with this technology?**

**Primary Integrations:**
- Google Workspace (Drive, Sheets, Calendar)
- OAuth 2.0 providers
- CDN for static assets (future)
- Email service for notifications (future)
- Analytics (future)

**Infrastructure:**
- Docker/Docker Compose
- Nginx reverse proxy
- Let's Encrypt SSL
- PostgreSQL database
- Redis for caching (future)

**Your integration focus:** PRPs should detail integration points and provide working examples.

---

## ADDITIONAL NOTES:

**Any other specific requirements, constraints, or considerations for this template?**

**PRP Format Requirements:**
- Must include pre-implementation checklist
- Always specify git branch naming
- Include rollback procedures
- Provide production deployment commands
- Update tracking in TASK.md and DEV_LOG files

**Code Standards:**
- TypeScript for all frontend code
- Type hints for Python code
- Comprehensive error handling
- Descriptive logging at key points
- Comments for complex logic

**Your additional notes:** PRPs should be self-contained documents that any developer can follow without additional context.

---

## TEMPLATE COMPLEXITY LEVEL:

**What level of complexity should this template target?**

- [ ] **Beginner-friendly** - Simple getting started patterns
- [X] **Intermediate** - Production-ready patterns with common features  
- [X] **Advanced** - Comprehensive patterns including complex scenarios
- [ ] **Enterprise** - Full enterprise patterns with monitoring, scaling, security

**Your choice:** Intermediate to Advanced - PRPs should provide production-ready code with comprehensive error handling, testing procedures, and deployment steps. They should be detailed enough for junior developers to follow but sophisticated enough to handle complex real-world scenarios.

---

## PRP GENERATION GUIDELINES:

When generating PRPs for Soleil, ensure each PRP includes:

1. **Header Section**:
   - Name (descriptive title)
   - Description (2-3 sentences explaining the task)
   - Priority/Impact level

2. **Pre-Implementation Requirements**:
   - Documentation to read
   - Git branch creation commands
   - Current state verification

3. **Clear Sections**:
   - Goal
   - Why (business justification)
   - Success Criteria (checkboxes)
   - Investigation Steps (if debugging)
   - Implementation Tasks (numbered with code examples)
   - Testing & Validation
   - Rollback Plan
   - Post-Deployment steps

4. **Code Examples**:
   - Complete, runnable code snippets
   - File paths clearly specified
   - Comments explaining complex parts
   - Error handling included

5. **Testing Procedures**:
   - Local testing commands
   - Production deployment steps
   - Validation checklist
   - Monitoring instructions

**REMINDER: Each PRP should be a complete, self-contained guide that enables successful implementation without requiring additional context or clarification.**