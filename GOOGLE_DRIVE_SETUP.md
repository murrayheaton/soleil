# Google Drive Setup Guide for Soleil

## 🎯 Overview
This guide will help you connect your murray@projectbrass.live Google Drive to the Soleil platform.

## 📋 Prerequisites
- Access to Google Cloud Console with murray@projectbrass.live
- A Google Drive folder structure set up for your band
- Admin access to create service accounts

## 🔧 Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Enable APIs and Services"
   - Search for "Google Drive API" and enable it
4. Create Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name: "soleil-drive-service"
   - Role: Skip for now (we'll use Drive sharing instead)
   - Click "Done"

## 🔑 Step 2: Generate Service Account Key

1. Click on the service account you created
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Choose JSON format
5. Save the file as `soleil-service-account.json` in a secure location

## 📁 Step 3: Share Your Google Drive Folder

1. Go to your Google Drive
2. Find your band's source folder
3. Right-click > "Share"
4. Add the service account email (found in the JSON file as "client_email")
5. Give it "Viewer" permissions (or "Editor" if you want the app to create folders)

## 🔍 Step 4: Get Your Folder ID

1. Open your source folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE`
3. Copy the folder ID after `/folders/`

## ⚙️ Step 5: Configure the Backend

1. Copy the .env.example to .env:
   ```bash
   cd band-platform/backend
   cp .env.example .env
   ```

2. Edit .env and add these Google-specific settings:
   ```env
   # Add these lines to your .env file:
   GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/soleil-service-account.json
   GOOGLE_DRIVE_SOURCE_FOLDER_ID=your_folder_id_from_step_4
   
   # For OAuth (future user authentication):
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

## 🚀 Step 6: Test the Connection

1. Start the backend with your real configuration:
   ```bash
   cd band-platform/backend
   source venv_linux/bin/activate
   pip install -r requirements.txt  # If not done already
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. Test the folder initialization endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/folders/initialize \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user", "instrument": "trumpet"}'
   ```

## 📝 Example Folder Structure

Your Google Drive should look like:
```
Band Drive (murray@projectbrass.live)
└── Source/
    ├── Charts/
    │   ├── AllOfMe_Bb.pdf
    │   ├── AllOfMe_Eb.pdf
    │   ├── BlueMoon_Bb.pdf
    │   └── BlueMoon_BassClef.pdf
    └── Audio/
        ├── AllOfMe.mp3
        └── BlueMoon.mp3
```

## 🎺 Test User View

After setup, a trumpet player will see:
```
Test User's Files/
├── All Of Me/
│   ├── AllOfMe_Bb.pdf
│   └── AllOfMe.mp3
└── Blue Moon/
    ├── BlueMoon_Bb.pdf
    └── BlueMoon.mp3
```

## ❓ Troubleshooting

### "Permission Denied" Error
- Make sure you shared the folder with the service account email
- Check that the service account email is correct (from the JSON file)

### "Folder Not Found" Error  
- Double-check the folder ID in your .env file
- Ensure the folder is not in trash
- Verify the service account has access

### Missing Dependencies
- Run: `pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2`

## 🔒 Security Notes

- Keep your service account JSON file secure
- Never commit it to git (it's in .gitignore)
- Rotate keys periodically
- Use environment variables for all sensitive data

---

Ready to test? Make sure you have:
- [ ] Service account JSON file saved
- [ ] Folder shared with service account
- [ ] Folder ID copied
- [ ] .env file configured
- [ ] Backend dependencies installed