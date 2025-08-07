# Security Setup for Sole Power Live

## Environment Variables

For security reasons, OAuth credentials and API keys are not included in the repository. You need to set them up locally:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   - `GOOGLE_CLIENT_ID`: Your Google OAuth2 client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth2 client secret
   - `GOOGLE_REDIRECT_URI`: Defaults to the production callback but falls back to `http://localhost:8000/api/auth/google/callback` when `DEBUG=true`
   - `CORS_ORIGINS`: Defaults include `https://solepower.live`, `https://www.solepower.live`, and localhost variants (`http://localhost`, `http://localhost:3000`, `http://localhost:8000`)
   - `GOOGLE_DRIVE_SOURCE_FOLDER_ID`: The ID of your Google Drive folder containing charts

## Files Not in Repository

The following files are gitignored for security:
- `google_token.json` - OAuth tokens (created after first login)
- `user_profiles.json` - User profile data (created after first user setup)
- `.env` - Your actual environment variables

## Getting OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Add `http://localhost:8000/api/auth/google/callback` to authorized redirect URIs
6. Copy the client ID and secret to your `.env` file

## Security Best Practices

- Never commit `.env` files or tokens to git
- Rotate credentials regularly
- Use different credentials for development and production
- Keep `.gitignore` updated with sensitive files
