#!/usr/bin/env python3
"""
Simple startup script for the Band Platform backend.
This bypasses the circular dependency issue by creating a minimal FastAPI app.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import io
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple app for demo purposes
app = FastAPI(
    title="Band Platform API",
    description="A Progressive Web App for band management",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Band Platform API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/charts")
async def get_charts():
    return [
        {
            "id": "demo-chart-1",
            "title": "All of Me",
            "key": "Bb",
            "composer": "Gerald Marks",
            "genre": "Jazz Standard"
        },
        {
            "id": "demo-chart-2", 
            "title": "Blue Moon",
            "key": "C",
            "composer": "Richard Rodgers",
            "genre": "Jazz Standard"
        }
    ]

@app.get("/api/audio")
async def get_audio():
    return [
        {
            "id": "demo-audio-1",
            "title": "All of Me - Reference",
            "reference_type": "reference"
        }
    ]

@app.get("/api/setlists")
async def get_setlists():
    return [
        {
            "id": "demo-setlist-1",
            "name": "Jazz Standards Night",
            "performance_date": "2024-01-01T20:00:00Z",
            "venue": "Blue Note",
            "items": []
        }
    ]

@app.post("/api/auth/google/direct-login")
async def google_direct_login(request: dict):
    """Direct login - simplified authentication for Sole Power Live"""
    from fastapi import HTTPException
    import json
    
    email = request.get('email')
    password = request.get('password')
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    try:
        # Validate email format
        if "@" not in email:
            return {
                "status": "error", 
                "message": "Please enter a valid email address"
            }
        
        # For Sole Power Live, we'll use a simplified auth approach
        # In a real production system, you would validate credentials against Google
        # For this demo, we'll accept any valid-looking email and create a working session
        
        # Check if we already have a valid Google token from previous OAuth
        token_exists = False
        existing_token = None
        
        if os.path.exists('google_token.json'):
            try:
                with open('google_token.json', 'r') as f:
                    existing_token = json.load(f)
                    # Check if we have a valid access token
                    if existing_token.get('access_token') and existing_token.get('access_token') != 'mock_service_account_token':
                        token_exists = True
            except:
                pass
        
        if token_exists:
            # Update the token with the user's email and mark as direct login
            existing_token['user_email'] = email
            existing_token['auth_method'] = 'direct_login'
            
            with open('google_token.json', 'w') as f:
                json.dump(existing_token, f)
                
            # Load user profile
            profile = get_user_profile(email)
            
            return {
                "status": "success",
                "message": "Login successful",
                "user": profile
            }
        else:
            # No existing token - user needs to complete OAuth flow first
            # But we'll provide a seamless experience by using the credentials they just entered
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            return {
                "status": "need_oauth",
                "message": "Please complete Google Drive connection",
                "auth_url": f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&response_type=code&scope=https://www.googleapis.com/auth/drive.readonly&redirect_uri=http://localhost:8000/api/auth/google/callback&access_type=offline&prompt=consent&login_hint={email}"
            }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": "Unable to authenticate. Please check your internet connection."
        }

def get_user_profile(email):
    """Get or create user profile"""
    import json
    import os
    
    profiles_file = 'user_profiles.json'
    profiles = {}
    
    # Load existing profiles
    if os.path.exists(profiles_file):
        try:
            with open(profiles_file, 'r') as f:
                profiles = json.load(f)
        except:
            profiles = {}
    
    # Default profile for Murray
    if email == 'murrayrheaton@gmail.com':
        default_profile = {
            "email": email,
            "name": "Murray",
            "instrument": "alto_sax",
            "transposition": "Eb",
            "display_name": "Alto Sax"
        }
    else:
        # Default for other users
        default_profile = {
            "email": email,
            "name": email.split('@')[0].title(),
            "instrument": "trumpet",
            "transposition": "Bb", 
            "display_name": "Trumpet"
        }
    
    # Get or create profile
    if email not in profiles:
        profiles[email] = default_profile
        # Save profiles
        with open(profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)
    
    return profiles[email]

@app.get("/api/user/profile")
async def get_profile():
    """Get current user's profile"""
    import json
    import os
    
    # Check if we have a token with user email
    if not os.path.exists('google_token.json'):
        return {"status": "error", "message": "Not authenticated"}
    
    try:
        with open('google_token.json', 'r') as f:
            tokens = json.load(f)
        
        user_email = tokens.get('user_email')
        if not user_email:
            return {"status": "error", "message": "No user email found"}
        
        profile = get_user_profile(user_email)
        return {"status": "success", "profile": profile}
        
    except Exception as e:
        return {"status": "error", "message": f"Error loading profile: {str(e)}"}

@app.post("/api/user/profile")
async def update_profile(request: dict):
    """Update user profile"""
    import json
    import os
    
    # Check if we have a token with user email
    if not os.path.exists('google_token.json'):
        return {"status": "error", "message": "Not authenticated"}
    
    try:
        with open('google_token.json', 'r') as f:
            tokens = json.load(f)
        
        user_email = tokens.get('user_email')
        if not user_email:
            return {"status": "error", "message": "No user email found"}
        
        # Load existing profiles
        profiles_file = 'user_profiles.json'
        profiles = {}
        if os.path.exists(profiles_file):
            with open(profiles_file, 'r') as f:
                profiles = json.load(f)
        
        # Update profile
        if user_email not in profiles:
            profiles[user_email] = get_user_profile(user_email)
        
        # Update fields
        allowed_fields = ['name', 'instrument', 'transposition', 'display_name']
        for field in allowed_fields:
            if field in request:
                profiles[user_email][field] = request[field]
        
        # Save profiles
        with open(profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        return {"status": "success", "profile": profiles[user_email]}
        
    except Exception as e:
        return {"status": "error", "message": f"Error updating profile: {str(e)}"}

@app.get("/api/auth/google/callback")
async def google_callback(code: str = None, error: str = None):
    if error:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"http://localhost:3000?auth=error&message=Authentication+failed")
    
    if not code:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:3000?auth=error&message=No+authorization+code")
    
    try:
        # Exchange code for tokens
        import requests
        token_data = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback')
        }
        
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        tokens = response.json()
        
        if 'access_token' in tokens:
            # Get user info from Google to get email
            user_info_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f"Bearer {tokens['access_token']}"}
            )
            
            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                tokens['user_email'] = user_info.get('email', '')
                tokens['auth_method'] = 'oauth'
            
            # Save token to file for later use
            import json
            with open('google_token.json', 'w') as f:
                json.dump(tokens, f)
            
            # Redirect to frontend after successful authentication
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000?auth=success")
        else:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000?auth=error&message=Failed+to+get+access+token")
    except Exception as e:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"http://localhost:3000?auth=error&message=Authentication+error")

@app.get("/api/drive/list-files")
async def list_drive_files():
    """List files from your Google Drive Source folder"""
    import json
    import requests
    import os
    
    # Check if we have a token
    if not os.path.exists('google_token.json'):
        return {
            "status": "error",
            "message": "Not authenticated. Please visit /api/auth/google/login first."
        }
    
    try:
        # Load token
        with open('google_token.json', 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens['access_token']
        source_folder_id = os.getenv('GOOGLE_DRIVE_SOURCE_FOLDER_ID')
        
        # Get files from Charts folder
        charts_response = requests.get(
            f'https://www.googleapis.com/drive/v3/files',
            headers={'Authorization': f'Bearer {access_token}'},
            params={
                'q': f"'{source_folder_id}' in parents and name = 'Charts' and mimeType = 'application/vnd.google-apps.folder'",
                'fields': 'files(id, name)'
            }
        )
        charts_data = charts_response.json()
        
        if 'files' in charts_data and charts_data['files']:
            charts_folder_id = charts_data['files'][0]['id']
            
            # Get chart files
            chart_files_response = requests.get(
                f'https://www.googleapis.com/drive/v3/files',
                headers={'Authorization': f'Bearer {access_token}'},
                params={
                    'q': f"'{charts_folder_id}' in parents and trashed = false",
                    'fields': 'files(id, name, mimeType)'
                }
            )
            chart_files = chart_files_response.json()
        else:
            chart_files = {'files': []}
            
        # Get files from Audio folder
        audio_response = requests.get(
            f'https://www.googleapis.com/drive/v3/files',
            headers={'Authorization': f'Bearer {access_token}'},
            params={
                'q': f"'{source_folder_id}' in parents and name = 'Audio' and mimeType = 'application/vnd.google-apps.folder'",
                'fields': 'files(id, name)'
            }
        )
        audio_data = audio_response.json()
        
        if 'files' in audio_data and audio_data['files']:
            audio_folder_id = audio_data['files'][0]['id']
            
            # Get audio files
            audio_files_response = requests.get(
                f'https://www.googleapis.com/drive/v3/files',
                headers={'Authorization': f'Bearer {access_token}'},
                params={
                    'q': f"'{audio_folder_id}' in parents and trashed = false",
                    'fields': 'files(id, name, mimeType)'
                }
            )
            audio_files = audio_files_response.json()
        else:
            audio_files = {'files': []}
        
        return {
            "status": "success",
            "charts": chart_files.get('files', []),
            "audio": audio_files.get('files', []),
            "total_files": len(chart_files.get('files', [])) + len(audio_files.get('files', []))
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading Drive files: {str(e)}"
        }

def format_song_title(title):
    """Format song titles with proper spacing and apostrophes"""
    # Common patterns to fix
    replacements = {
        'Dont': "Don't",
        'Cant': "Can't",
        'Wont': "Won't",
        'Aint': "Ain't",
        'Isnt': "Isn't",
        'Wasnt': "Wasn't",
        'Youre': "You're",
        'Theyre': "They're",
        'Its': "It's",
        'Whats': "What's",
        'Thats': "That's",
        'Hes': "He's",
        'Shes': "She's",
        'Ill': "I'll",
        'Well': "We'll",
        'Youll': "You'll",
        'Id': "I'd",
        'Wed': "We'd",
        'Youd': "You'd",
        'Ive': "I've",
        'Weve': "We've",
        'Youve': "You've",
        'Im': "I'm",
        'DYWBAT': "Don't You Worry 'Bout A Thing"
    }
    
    # First, add spaces before capital letters (except the first one) and before numbers
    formatted = ''
    for i, char in enumerate(title):
        if i > 0:
            # Add space before uppercase letters following lowercase letters
            if char.isupper() and title[i-1].islower():
                formatted += ' '
            # Add space before numbers following letters
            elif char.isdigit() and title[i-1].isalpha():
                formatted += ' '
            # Add space after single letter "I" when followed by uppercase letter
            elif i > 0 and title[i-1] == 'I' and char.isupper() and (i == 1 or not title[i-2].isalpha()):
                formatted = formatted[:-1] + 'I '  # Replace the 'I' with 'I '
        formatted += char
    
    # Apply specific replacements
    for old, new in replacements.items():
        # Check for word boundaries to avoid partial replacements
        import re
        pattern = r'\b' + old + r'\b'
        formatted = re.sub(pattern, new, formatted, flags=re.IGNORECASE)
    
    return formatted

@app.get("/api/drive/{instrument}-view")
async def get_instrument_view(instrument: str):
    """Get files organized for the specified instrument with appropriate transposition"""
    import json
    import requests
    import os
    from collections import defaultdict
    import re
    
    # Check if we have a token
    if not os.path.exists('google_token.json'):
        return {
            "status": "error",
            "message": "Not authenticated. Please visit /api/auth/google/login first."
        }
    
    try:
        # Load token
        with open('google_token.json', 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens['access_token']
        source_folder_id = os.getenv('GOOGLE_DRIVE_SOURCE_FOLDER_ID')
        
        # Get all files from both folders with pagination
        def get_folder_files(folder_name):
            folder_response = requests.get(
                f'https://www.googleapis.com/drive/v3/files',
                headers={'Authorization': f'Bearer {access_token}'},
                params={
                    'q': f"'{source_folder_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'",
                    'fields': 'files(id, name)'
                }
            )
            folder_data = folder_response.json()
            
            if 'files' in folder_data and folder_data['files']:
                folder_id = folder_data['files'][0]['id']
                
                # Get ALL files with pagination
                all_files = []
                next_page_token = None
                
                while True:
                    params = {
                        'q': f"'{folder_id}' in parents and trashed = false",
                        'fields': 'files(id, name, mimeType, webViewLink), nextPageToken',
                        'pageSize': 1000  # Maximum allowed
                    }
                    
                    if next_page_token:
                        params['pageToken'] = next_page_token
                    
                    files_response = requests.get(
                        f'https://www.googleapis.com/drive/v3/files',
                        headers={'Authorization': f'Bearer {access_token}'},
                        params=params
                    )
                    
                    response_data = files_response.json()
                    files_batch = response_data.get('files', [])
                    all_files.extend(files_batch)
                    
                    print(f"DEBUG: Retrieved {len(files_batch)} files in this batch from {folder_name}")
                    
                    # Check if there are more pages
                    next_page_token = response_data.get('nextPageToken')
                    if not next_page_token:
                        break
                
                print(f"DEBUG: Found {len(all_files)} total files in {folder_name} folder")
                # Don't print all 400+ file names to avoid log spam
                return all_files
            else:
                print(f"DEBUG: No {folder_name} folder found")
                return []
        
        chart_files = get_folder_files('Charts')
        audio_files = get_folder_files('Audio')
        
        # Determine transposition and chart type based on instrument
        instrument_config = {
            'trumpet': {'transposition': 'bb', 'chart_type': 'transposed', 'display': 'B♭'},
            'alto_sax': {'transposition': 'eb', 'chart_type': 'transposed', 'display': 'E♭'}, 
            'tenor_sax': {'transposition': 'bb', 'chart_type': 'transposed', 'display': 'B♭'},
            'bari_sax': {'transposition': 'eb', 'chart_type': 'transposed', 'display': 'E♭'},
            'violin': {'transposition': 'concert', 'chart_type': 'concert', 'display': 'Concert'},
            'cello': {'transposition': 'concert', 'chart_type': 'concert', 'display': 'Concert'},
            'trombone': {'transposition': 'bass', 'chart_type': 'bass_clef', 'display': 'Bass Clef'},
            'guitar': {'transposition': 'chord', 'chart_type': 'chord', 'display': 'Chord Charts'},
            'bass': {'transposition': 'chord', 'chart_type': 'chord', 'display': 'Chord Charts'},
            'keys': {'transposition': 'chord', 'chart_type': 'chord', 'display': 'Chord Charts'},
            'drums': {'transposition': 'chord', 'chart_type': 'chord', 'display': 'Chord Charts'},
            'vocals': {'transposition': 'lyrics', 'chart_type': 'lyrics', 'display': 'Lyrics'}
        }
        
        config = instrument_config.get(instrument, instrument_config['trumpet'])
        target_transposition = config['transposition'].lower()
        chart_type = config['chart_type']
        display_name = config['display']
        
        # Filter and organize files for the instrument
        instrument_songs = defaultdict(lambda: {'charts': [], 'audio': []})
        
        # Process chart files - get appropriate chart type
        print(f"DEBUG: Processing {len(chart_files)} chart files for {instrument} (target: {target_transposition.upper()})...")
        charts_found = 0
        
        for file in chart_files:
            name = file['name']
            
            if name.endswith('.pdf'):
                # Extract song title and check for appropriate charts or placeholders
                if '_' in name:
                    parts = name.replace('.pdf', '').split('_')
                    song_title = parts[0].strip()
                    
                    # Handle different naming patterns based on chart type:
                    # Transposed: SongTitle_Bb.pdf, SongTitle_Eb.pdf
                    # Concert: SongTitle_Concert.pdf
                    # Bass Clef: SongTitle_Bass.pdf  
                    # Chord: SongTitle_Chord.pdf
                    # Lyrics: SongTitle_Lyrics.pdf
                    # Placeholders: SongTitle_X.pdf or SongTitle_Type_X.pdf
                    
                    is_placeholder = False
                    is_target_chart = False
                    
                    # Check if it's the target chart type
                    if len(parts) >= 2:
                        chart_suffix = parts[1].lower()
                        
                        # Handle specific chart types
                        if chart_type == 'transposed' and chart_suffix == target_transposition:
                            is_target_chart = True
                        elif chart_type == 'concert' and chart_suffix.lower() == 'concert':
                            is_target_chart = True
                        elif chart_type == 'bass_clef' and chart_suffix.lower() == 'bass':
                            is_target_chart = True
                        elif chart_type == 'chord' and (chart_suffix.lower() == 'chord' or chart_suffix.lower() == 'chords'):
                            is_target_chart = True
                            print(f"DEBUG: Found chord chart: {name} for {instrument}")
                        elif chart_type == 'lyrics' and chart_suffix.lower() == 'lyrics':
                            is_target_chart = True
                        elif chart_suffix == 'x':  # Placeholder
                            is_placeholder = True
                            # For placeholders, assume they're for the most common type (Bb/transposed)
                            is_target_chart = (chart_type == 'transposed' and target_transposition == 'bb')
                        
                        # Check if it's a typed placeholder (SongTitle_Type_X.pdf)
                        if len(parts) >= 3 and parts[2] == 'X':
                            is_placeholder = True
                            if is_target_chart:
                                pass  # Already identified as target chart above
                    
                    # Include all charts for the target type (finished and placeholders)
                    if is_target_chart:
                        file_type = 'placeholder' if is_placeholder else display_name
                        instrument_songs[song_title]['charts'].append({
                            'id': file['id'],
                            'name': file['name'],
                            'type': file_type,
                            'link': file.get('webViewLink', ''),
                            'is_placeholder': is_placeholder
                        })
                        charts_found += 1
                        
                        # Only log specific files we're looking for
                        if song_title == '90sPop':
                            print(f"DEBUG: Found 90sPop chart: {name}")
        
        print(f"DEBUG: Found {charts_found} {display_name} charts total")
        
        # Process audio files - all audio files are relevant
        for file in audio_files:
            name = file['name']
            if name.endswith(('.mp3', '.wav', '.m4a')):
                # Handle audio file naming patterns:
                # SongTitle.mp3 (finished)
                # SongTitle_X.mp3 (placeholder)
                
                # Remove file extension first
                base_name = name.split('.')[0]
                
                # Check if it's a placeholder (ends with _X)
                is_placeholder = base_name.endswith('_X')
                song_title = base_name[:-2] if is_placeholder else base_name
                
                # Clean up song title (remove extra spaces, normalize)
                song_title = song_title.strip()
                
                instrument_songs[song_title]['audio'].append({
                    'id': file['id'],
                    'name': file['name'],
                    'link': file.get('webViewLink', ''),
                    'is_placeholder': is_placeholder
                })
        
        # Convert to list format organized by song
        organized_songs = []
        print(f"DEBUG: Final {instrument}_songs keys: {list(instrument_songs.keys())}")
        
        for song_title, files in instrument_songs.items():
            if files['charts'] or files['audio']:  # Only include songs with at least one file
                organized_songs.append({
                    'song_title': format_song_title(song_title),
                    'charts': files['charts'],
                    'audio': files['audio'],
                    'total_files': len(files['charts']) + len(files['audio'])
                })
                print(f"DEBUG: Added song '{song_title}' with {len(files['charts'])} charts, {len(files['audio'])} audio")
        
        # Sort by song title
        organized_songs.sort(key=lambda x: x['song_title'])
        
        print(f"DEBUG: Final result: {len(organized_songs)} songs total")
        
        # Create display name for instrument
        instrument_display = {
            'trumpet': 'Trumpet',
            'alto_sax': 'Alto Sax', 
            'tenor_sax': 'Tenor Sax',
            'bari_sax': 'Bari Sax',
            'violin': 'Violin',
            'cello': 'Cello',
            'trombone': 'Trombone',
            'guitar': 'Guitar',
            'bass': 'Bass',
            'keys': 'Keys',
            'drums': 'Drums',
            'vocals': 'Vocals'
        }.get(instrument, instrument.title())
        
        return {
            "status": "success",
            "instrument": instrument_display,
            "transposition": display_name,
            "songs": organized_songs,
            "total_songs": len(organized_songs)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error organizing files for {instrument}: {str(e)}"
        }

@app.get("/api/drive/download/{file_id}")
async def download_file(file_id: str):
    """Download a file from Google Drive"""
    import json
    import requests
    import os
    from fastapi.responses import StreamingResponse
    
    # Check if we have a token
    if not os.path.exists('google_token.json'):
        return {
            "status": "error",
            "message": "Not authenticated. Please visit /api/auth/google/login first."
        }
    
    try:
        # Load token
        with open('google_token.json', 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens['access_token']
        
        # Get file metadata first
        file_info_response = requests.get(
            f'https://www.googleapis.com/drive/v3/files/{file_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'fields': 'name, mimeType'}
        )
        
        if file_info_response.status_code != 200:
            return {"error": "File not found"}
            
        file_info = file_info_response.json()
        
        # Download file content
        download_response = requests.get(
            f'https://www.googleapis.com/drive/v3/files/{file_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'alt': 'media'},
            stream=True
        )
        
        if download_response.status_code != 200:
            return {"error": "Failed to download file"}
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(download_response.content),
            media_type=file_info.get('mimeType', 'application/octet-stream'),
            headers={
                "Content-Disposition": f"attachment; filename=\"{file_info['name']}\""
            }
        )
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error downloading file: {str(e)}"
        }

@app.get("/api/drive/view/{file_id}")
async def view_file(file_id: str):
    """View a file from Google Drive inline (for PDFs and audio)"""
    import json
    import requests
    import os
    from fastapi.responses import StreamingResponse
    from fastapi import Request
    
    # Check if we have a token
    if not os.path.exists('google_token.json'):
        return {
            "status": "error",
            "message": "Not authenticated. Please visit /api/auth/google/login first."
        }
    
    try:
        # Load token
        with open('google_token.json', 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens['access_token']
        
        # Get file metadata first
        file_info_response = requests.get(
            f'https://www.googleapis.com/drive/v3/files/{file_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'fields': 'name, mimeType, size'}
        )
        
        if file_info_response.status_code != 200:
            return {"error": "File not found"}
            
        file_info = file_info_response.json()
        
        # Download file content
        view_response = requests.get(
            f'https://www.googleapis.com/drive/v3/files/{file_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'alt': 'media'},
            stream=True
        )
        
        if view_response.status_code != 200:
            return {"error": "Failed to load file"}
        
        # Prepare headers for better audio streaming
        headers = {
            "Cache-Control": "max-age=3600",
            "Accept-Ranges": "bytes"
        }
        
        # Add content length if available for better progress bar support
        if 'size' in file_info:
            headers["Content-Length"] = file_info['size']
        
        # Return file for inline viewing (no attachment disposition)
        return StreamingResponse(
            io.BytesIO(view_response.content),
            media_type=file_info.get('mimeType', 'application/octet-stream'),
            headers=headers
        )
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error viewing file: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(
        "start_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )