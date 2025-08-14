#!/usr/bin/env python3
"""
SOLEil Real-Time Development Dashboard
Shows actual file changes, code being written, and real development progress
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
import threading

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

class DevelopmentMonitor:
    """Monitors actual file changes and development progress"""
    
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
        event_handler = FileChangeHandler(self)
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
                print(f"🔍 Monitoring: {directory}")
        
        observer.start()
        return observer
    
    def record_file_change(self, file_path, change_type, content_preview=""):
        """Record a real file change"""
        timestamp = datetime.now()
        
        change = {
            'timestamp': timestamp,
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
            return "No development activity detected"
        
        recent_changes = [c for c in self.file_changes if (datetime.now() - c['timestamp']).seconds < 300]
        
        if not recent_changes:
            return "No recent development activity (last 5 minutes)"
        
        # Analyze what's actually being worked on
        files_being_worked = set()
        for change in recent_changes:
            if change['change_type'] in ['created', 'modified']:
                files_being_worked.add(change['file_path'])
        
        return {
            'active_files': len(files_being_worked),
            'recent_changes': len(recent_changes),
            'last_activity': self.code_metrics['last_activity'].strftime('%H:%M:%S') if self.code_metrics['last_activity'] else 'Never',
            'files_being_worked': list(files_being_worked)[:5]  # Show top 5
        }

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system change events"""
    
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

class RealTimeDashboard:
    """Real-time development dashboard"""
    
    def __init__(self):
        self.monitor = DevelopmentMonitor()
        self.running = False
        
    async def start(self):
        """Start the real-time dashboard"""
        print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Real-Time Development Dashboard               ║
    ║              Live Code Changes & Progress                ║
    ╚═══════════════════════════════════════════════════════════╝
        """)
        
        # Start file monitoring
        observer = self.monitor.start_file_monitoring()
        
        print("🚀 Real-time development monitoring started!")
        print("📊 Monitoring actual file changes, code being written, and real progress")
        print("\nPress Ctrl+C to stop monitoring")
        
        self.running = True
        
        try:
            # Main monitoring loop
            while self.running:
                await self.display_dashboard()
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping development monitoring...")
            observer.stop()
            observer.join()
            self.running = False
    
    async def display_dashboard(self):
        """Display the current development dashboard"""
        # Clear screen (simple approach)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Real-Time Development Dashboard               ║
    ║              Live Code Changes & Progress                ║
    ╚═══════════════════════════════════════════════════════════╝
        """)
        
        # Get real progress
        real_progress = self.monitor.get_real_progress()
        
        # Handle case where real_progress might be a string
        if isinstance(real_progress, str):
            print(f"📊 Status: {real_progress}")
            active_files = 0
            recent_changes = 0
            last_activity = "Never"
        else:
            active_files = real_progress.get('active_files', 0)
            recent_changes = real_progress.get('recent_changes', 0)
            last_activity = real_progress.get('last_activity', 'Never')
        
        # Display current status
        print(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        print(f"📁 Files Being Worked On: {active_files}")
        print(f"🔄 Recent Changes: {recent_changes}")
        print(f"⏰ Last Activity: {last_activity}")
        
        # Show recent file changes
        print(f"\n📝 Recent File Changes:")
        recent_changes = self.monitor.file_changes[-10:]  # Last 10 changes
        
        if recent_changes:
            for change in reversed(recent_changes):
                timestamp = change['timestamp'].strftime('%H:%M:%S')
                change_icon = "🆕" if change['change_type'] == 'created' else "✏️" if change['change_type'] == 'modified' else "🗑️"
                print(f"  {change_icon} {timestamp} | {change['file_path']}")
                if change['content_preview']:
                    print(f"     Preview: {change['content_preview']}")
        else:
            print("  No file changes detected yet")
        
        # Show files currently being worked on
        if isinstance(real_progress, dict) and 'files_being_worked' in real_progress:
            print(f"\n🔨 Files Currently Being Worked On:")
            for file_path in real_progress['files_being_worked']:
                print(f"  📄 {file_path}")
        elif isinstance(real_progress, str):
            print(f"\n🔨 Files Currently Being Worked On:")
            print(f"  📄 {real_progress}")
        else:
            print(f"\n🔨 Files Currently Being Worked On:")
            print(f"  📄 No active files detected")
        
        # Show development metrics
        print(f"\n📊 Development Metrics:")
        print(f"  📁 Files Created: {self.monitor.code_metrics['files_created']}")
        print(f"  ✏️  Files Modified: {self.monitor.code_metrics['files_modified']}")
        print(f"  📏 Total Changes: {len(self.monitor.file_changes)}")
        
        # Show what's actually happening vs. what's claimed
        print(f"\n🎯 Real Development Status:")
        if self.monitor.code_metrics['last_activity']:
            time_since_activity = (datetime.now() - self.monitor.code_metrics['last_activity']).seconds
            if time_since_activity < 60:
                print(f"  🟢 ACTIVE: Code is being written right now!")
            elif time_since_activity < 300:
                print(f"  🟡 RECENT: Code was written {time_since_activity} seconds ago")
            else:
                print(f"  🔴 INACTIVE: No code changes for {time_since_activity//60} minutes")
        else:
            print(f"  🔴 NO ACTIVITY: No development detected")
        
        print(f"\n💡 Tip: This dashboard shows REAL file changes, not simulated completion")

async def main():
    """Main entry point"""
    dashboard = RealTimeDashboard()
    await dashboard.start()

if __name__ == "__main__":
    asyncio.run(main())
