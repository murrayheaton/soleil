# Authentication Module

**Version:** 1.0.0  
**Last Updated:** 2025-08-05  
**Status:** Active

## Purpose and Scope
The Authentication module manages user authentication, authorization, and session management for the SOLEil platform. It handles Google OAuth integration, JWT token management, and user profile operations.

## Module Context
This module is responsible for:
- Google OAuth 2.0 authentication flow
- JWT token generation and validation
- User session management
- User profile CRUD operations
- Role-based access control

## Dependencies
- Core module (for EventBus and shared utilities)
- External: google-auth, python-jose, passlib

## API Endpoints (To Be Migrated)
- `POST /api/auth/google` - Google OAuth callback
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/logout` - Logout user

## Key Services (To Be Migrated)
- `AuthService` - Core authentication logic
- `TokenService` - JWT token management
- `UserService` - User profile operations
- `GoogleAuthService` - Google OAuth integration

## Events Published
- `user.login` - User successfully logged in
- `user.logout` - User logged out
- `user.profile.updated` - User profile updated
- `user.created` - New user created

## Events Subscribed
- None initially

## Testing Strategy
- Unit tests for token generation/validation
- Integration tests for OAuth flow
- Mock Google OAuth responses
- Test role-based access control

## Module-Specific Rules
1. All passwords must be hashed using bcrypt
2. JWT tokens must have appropriate expiration
3. Refresh tokens must be stored securely
4. OAuth state must be validated
5. User sessions must be properly managed