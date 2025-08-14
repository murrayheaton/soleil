#!/usr/bin/env python3
"""
SOLEil Web-Based Development Dashboard
Real-time development progress in your browser
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, render_template_string, jsonify
import threading
import webbrowser

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)

class WebDevelopmentMonitor:
    """Monitors actual file changes and development progress for web dashboard"""
    
    def __init__(self):
        self.file_changes = []
        self.code_metrics = {
            'lines_added': 0,
            'lines_modified': 0,
            'files_created': 0,
            'files_modified': 0,
            'last_activity': None
        }
        self.active_developers = set()
        self.current_tasks = {}
        self.real_progress = {}
        
    def start_file_monitoring(self):
        """Start monitoring file system changes"""
        event_handler = WebFileChangeHandler(self)
        observer = Observer()
        
        # Monitor key development directories
        directories_to_watch = [
            "band-platform/backend/modules",
            "band-platform/frontend/src",
            "PRPs/active",
            "agent_deployment"
        ]
        
        for directory in directories_to_watch:
            if Path(directory).exists():
                observer.schedule(event_handler, directory, recursive=True)
                print(f"🔍 Web Monitoring: {directory}")
        
        observer.start()
        return observer
    
    def record_file_change(self, file_path, change_type, content_preview=""):
        """Record a real file change"""
        timestamp = datetime.now()
        
        change = {
            'timestamp': timestamp.isoformat(),
            'file_path': str(file_path),
            'change_type': change_type,
            'content_preview': content_preview[:200] + "..." if len(content_preview) > 200 else content_preview,
            'size_bytes': Path(file_path).stat().st_size if Path(file_path).exists() else 0
        }
        
        self.file_changes.append(change)
        
        # Update metrics
        if change_type == 'created':
            self.code_metrics['files_created'] += 1
        elif change_type == 'modified':
            self.code_metrics['files_modified'] += 1
        
        self.code_metrics['last_activity'] = timestamp
        
        # Keep only last 100 changes
        if len(self.file_changes) > 100:
            self.file_changes = self.file_changes[-100:]
    
    def get_real_progress(self):
        """Get actual development progress based on real changes"""
        if not self.file_changes:
            return {"status": "No development activity detected"}
        
        recent_changes = [c for c in self.file_changes if (datetime.now() - datetime.fromisoformat(c['timestamp'])).seconds < 300]
        
        if not recent_changes:
            return {"status": "No recent development activity (last 5 minutes)"}
        
        # Analyze what's actually being worked on
        files_being_worked = set()
        for change in recent_changes:
            if change['change_type'] in ['created', 'modified']:
                files_being_worked.add(change['file_path'])
        
        return {
            'active_files': len(files_being_worked),
            'recent_changes': len(recent_changes),
            'last_activity': self.code_metrics['last_activity'].isoformat() if self.code_metrics['last_activity'] else None,
            'files_being_worked': list(files_being_worked)[:10],
            'status': 'active'
        }

class WebFileChangeHandler(FileSystemEventHandler):
    """Handles file system change events for web dashboard"""
    
    def __init__(self, monitor):
        self.monitor = monitor
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor.record_file_change(event.src_path, 'created')
    
    def on_modified(self, event):
        if not event.is_directory:
            # Read file content for preview
            try:
                with open(event.src_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.monitor.record_file_change(event.src_path, 'modified', content)
            except Exception as e:
                self.monitor.record_file_change(event.src_path, 'modified', f"[Error reading content: {e}]")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.monitor.record_file_change(event.src_path, 'deleted')

# Global monitor instance
web_monitor = WebDevelopmentMonitor()

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SOLEil Real-Time Development Dashboard</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .status-card h3 {
            margin-top: 0;
            color: #ffd700;
        }
        .metric {
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }
        .file-changes {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        .file-change {
            background: rgba(255,255,255,0.1);
            margin: 10px 0;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #00ff88;
        }
        .file-change.created { border-left-color: #00ff88; }
        .file-change.modified { border-left-color: #ffd700; }
        .file-change.deleted { border-left-color: #ff6b6b; }
        .timestamp {
            color: #ccc;
            font-size: 0.9em;
        }
        .file-path {
            font-weight: bold;
            color: #fff;
        }
        .content-preview {
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
            color: #ddd;
        }
        .activity-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .activity-active { background: #00ff88; }
        .activity-recent { background: #ffd700; }
        .activity-inactive { background: #ff6b6b; }
        .refresh-info {
            text-align: center;
            margin-top: 20px;
            color: #ccc;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SOLEil Real-Time Development Dashboard</h1>
            <p>Live Code Changes & Progress Monitoring</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📁 Files Being Worked On</h3>
                <div class="metric" id="active-files">0</div>
                <p>Currently active development files</p>
            </div>
            
            <div class="status-card">
                <h3>🔄 Recent Changes</h3>
                <div class="metric" id="recent-changes">0</div>
                <p>Changes in last 5 minutes</p>
            </div>
            
            <div class="status-card">
                <h3>📁 Total Files Created</h3>
                <div class="metric" id="files-created">0</div>
                <p>New files added</p>
            </div>
            
            <div class="status-card">
                <h3>✏️ Total Files Modified</h3>
                <div class="metric" id="files-modified">0</div>
                <p>Existing files changed</p>
            </div>
        </div>
        
        <div class="status-card">
            <h3>🎯 Development Status</h3>
            <div id="dev-status">
                <span class="activity-indicator" id="activity-indicator"></span>
                <span id="status-text">Loading...</span>
            </div>
        </div>
        
        <div class="file-changes">
            <h3>📝 Recent File Changes</h3>
            <div id="file-changes-list">
                <p>Loading file changes...</p>
            </div>
        </div>
        
        <div class="refresh-info">
            <p>Dashboard updates every 2 seconds • Last update: <span id="last-update">Never</span></p>
        </div>
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update metrics
                    document.getElementById('active-files').textContent = data.active_files || 0;
                    document.getElementById('recent-changes').textContent = data.recent_changes || 0;
                    document.getElementById('files-created').textContent = data.files_created || 0;
                    document.getElementById('files-modified').textContent = data.files_modified || 0;
                    
                    // Update development status
                    const statusText = document.getElementById('status-text');
                    const activityIndicator = document.getElementById('activity-indicator');
                    
                    if (data.last_activity) {
                        const lastActivity = new Date(data.last_activity);
                        const now = new Date();
                        const timeDiff = Math.floor((now - lastActivity) / 1000);
                        
                        if (timeDiff < 60) {
                            statusText.textContent = '🟢 ACTIVE: Code is being written right now!';
                            activityIndicator.className = 'activity-indicator activity-active';
                        } else if (timeDiff < 300) {
                            statusText.textContent = `🟡 RECENT: Code was written ${timeDiff} seconds ago`;
                            activityIndicator.className = 'activity-indicator activity-recent';
                        } else {
                            statusText.textContent = `🔴 INACTIVE: No code changes for ${Math.floor(timeDiff/60)} minutes`;
                            activityIndicator.className = 'activity-indicator activity-inactive';
                        }
                    } else {
                        statusText.textContent = '🔴 NO ACTIVITY: No development detected';
                        activityIndicator.className = 'activity-indicator activity-inactive';
                    }
                    
                    // Update file changes
                    const fileChangesList = document.getElementById('file-changes-list');
                    if (data.file_changes && data.file_changes.length > 0) {
                        fileChangesList.innerHTML = data.file_changes.map(change => `
                            <div class="file-change ${change.change_type}">
                                <div class="timestamp">${new Date(change.timestamp).toLocaleTimeString()}</div>
                                <div class="file-path">${change.file_path}</div>
                                ${change.content_preview ? `<div class="content-preview">${change.content_preview}</div>` : ''}
                            </div>
                        `).join('');
                    } else {
                        fileChangesList.innerHTML = '<p>No file changes detected yet</p>';
                    }
                    
                    // Update last update time
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                });
        }
        
        // Update dashboard every 2 seconds
        setInterval(updateDashboard, 2000);
        
        // Initial update
        updateDashboard();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return DASHBOARD_HTML

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    real_progress = web_monitor.get_real_progress()
    
    return jsonify({
        'active_files': real_progress.get('active_files', 0),
        'recent_changes': real_progress.get('recent_changes', 0),
        'files_created': web_monitor.code_metrics['files_created'],
        'files_modified': web_monitor.code_metrics['files_modified'],
        'last_activity': web_monitor.code_metrics['last_activity'].isoformat() if web_monitor.code_metrics['last_activity'] else None,
        'file_changes': web_monitor.file_changes[-10:]  # Last 10 changes
    })

def start_web_dashboard():
    """Start the web-based dashboard"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Web-Based Development Dashboard               ║
    ║              Real-Time Progress in Browser               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Start file monitoring
    observer = web_monitor.start_file_monitoring()
    
    print("🚀 Web dashboard started!")
    print("📊 Open your browser to: http://localhost:5001")
    print("🔍 Monitoring actual file changes and development progress")
    
    # Open browser automatically
    webbrowser.open('http://localhost:5001')
    
    return observer

if __name__ == "__main__":
    # Start file monitoring in background
    observer = start_web_dashboard()
    
    try:
        # Start Flask app
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Stopping web dashboard...")
        observer.stop()
        observer.join()
