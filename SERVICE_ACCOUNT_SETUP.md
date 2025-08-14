# Google Drive Service Account Setup

## Overview
The SOLEil platform uses a Google Service Account to provide all band members access to a shared Google Drive folder containing charts and assets. This approach means:

- **Users don't need individual Google Drive permissions**
- **One shared Drive folder for all band assets**
- **Users authenticate with Google only for identity (login)**
- **The service account handles all Drive access**

## Architecture

```
Band Members (Multiple Users)
         ↓
    Google OAuth 
    (Identity Only)
         ↓
    SOLEil Backend
         ↓
    Service Account
         ↓
    Shared Band Google Drive
```

## Setup Instructions

### Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select or create a project for your band
3. Navigate to **IAM & Admin** > **Service Accounts**
4. Click **Create Service Account**
5. Enter details:
   - Name: `soleil-drive-service`
   - Description: `Service account for SOLEil band platform Drive access`
6. Click **Create and Continue**
7. Skip the optional steps and click **Done**

### Step 2: Generate Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Choose **JSON** format
5. Save the file as `service-account-key.json` in a secure location

### Step 3: Share Your Band's Google Drive Folder

1. Go to your Google Drive
2. Right-click on your band's assets folder
3. Click **Share**
4. Add the service account email (found in the JSON file as `client_email`)
   - Example: `soleil-drive-service@your-project.iam.gserviceaccount.com`
5. Give it **Viewer** permissions (or **Editor** if you want the app to create folders)
6. Click **Send**

### Step 4: Configure Environment Variables

Add these to your `.env` file:

```env
# Service Account for shared Drive access
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account-key.json

# Your band's shared Google Drive folder ID
GOOGLE_DRIVE_SOURCE_FOLDER_ID=your_folder_id_here

# OAuth for user authentication (login only)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
```

### Step 5: Get Your Folder ID

1. Open your band's folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE`
3. Copy the folder ID after `/folders/`
4. Add it to `GOOGLE_DRIVE_SOURCE_FOLDER_ID` in your `.env`

## Important Notes

### Security
- **Never commit the service account key file to git**
- Keep the service account key secure
- Add `service-account-key.json` to `.gitignore`
- Use environment variables for all sensitive data

### Permissions
- The service account only needs **read** access to the Drive folder
- Users authenticate with Google OAuth only for identity (name, email)
- Users don't need any Google Drive permissions themselves

### Folder Structure
Your band's Google Drive should be organized like:
```
Band Assets/                    (shared with service account)
├── Charts/
│   ├── AllOfMe_Bb.pdf
│   ├── AllOfMe_Eb.pdf
│   ├── AllOfMe_Concert.pdf
│   └── BlueBossa_Bb.pdf
└── Audio/
    ├── AllOfMe_Reference.mp3
    └── BlueBossa_Live.mp3
```

## Troubleshooting

### "Failed to authenticate with Google Drive service account"
- Check that `GOOGLE_SERVICE_ACCOUNT_FILE` points to the correct file
- Verify the service account key file exists and is valid JSON
- Ensure the file has proper read permissions

### "No charts found"
- Verify the folder ID in `GOOGLE_DRIVE_SOURCE_FOLDER_ID` is correct
- Check that the folder is shared with the service account email
- Ensure the folder contains PDF files with the correct naming convention

### "Access denied to folder"
- Make sure the service account has at least **Viewer** permissions
- Check that the folder isn't in trash
- Verify you're using the correct folder ID

## Benefits of This Approach

1. **Simplified Permissions**: Band members don't need individual Drive access
2. **Centralized Management**: One service account manages all Drive access
3. **Better Security**: Users never directly access the Drive API
4. **Easier Onboarding**: New members just need to create an account, no Drive sharing needed
5. **Consistent Access**: All users see the same files from the same source