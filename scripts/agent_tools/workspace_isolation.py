#!/usr/bin/env python3
"""
Agent Workspace Isolation Tool
Creates isolated working environments for each agent type
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set
import subprocess
import argparse

# Agent module mappings
AGENT_MODULES = {
    "auth": {
        "paths": [
            "band-platform/backend/modules/auth",
            "band-platform/frontend/src/modules/auth"
        ],
        "read_only": [
            "band-platform/backend/modules/core",
            "band-platform/backend/shared"
        ]
    },
    "content": {
        "paths": [
            "band-platform/backend/modules/content",
            "band-platform/frontend/src/modules/content"
        ],
        "read_only": [
            "band-platform/backend/modules/core",
            "band-platform/backend/shared"
        ]
    },
    "drive": {
        "paths": [
            "band-platform/backend/modules/drive",
            "band-platform/frontend/src/modules/drive"
        ],
        "read_only": [
            "band-platform/backend/modules/core",
            "band-platform/backend/shared"
        ]
    },
    "sync": {
        "paths": [
            "band-platform/backend/modules/sync",
            "band-platform/frontend/src/modules/sync"
        ],
        "read_only": [
            "band-platform/backend/modules/core",
            "band-platform/backend/shared"
        ]
    },
    "dashboard": {
        "paths": [
            "band-platform/backend/modules/dashboard",
            "band-platform/frontend/src/modules/dashboard"
        ],
        "read_only": [
            "band-platform/backend/modules/core",
            "band-platform/backend/shared"
        ]
    },
    "integration": {
        "paths": [
            "band-platform/backend/modules/core",
            "band-platform/backend/tests/integration",
            "MODULAR_ARCHITECTURE_PROPOSAL.md",
            "MODULES.md",
            "AGENT_GUIDE.md"
        ],
        "read_only": [
            "band-platform/backend/modules",
            "band-platform/frontend/src/modules"
        ]
    }
}


class WorkspaceIsolation:
    """Manages isolated workspaces for agents."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.workspaces_dir = base_path / ".agent_workspaces"
        self.workspaces_dir.mkdir(exist_ok=True)
        
    def create_workspace(self, agent_type: str) -> Path:
        """Create an isolated workspace for an agent."""
        if agent_type not in AGENT_MODULES:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Create workspace directory
        workspace_path = self.workspaces_dir / f"{agent_type}_workspace"
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        workspace_path.mkdir()
        
        # Copy writable paths
        for path in AGENT_MODULES[agent_type]["paths"]:
            src = self.base_path / path
            if src.exists():
                if src.is_file():
                    dst = workspace_path / path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                else:
                    dst = workspace_path / path
                    shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # Create symlinks for read-only paths
        for path in AGENT_MODULES[agent_type]["read_only"]:
            src = self.base_path / path
            if src.exists():
                dst = workspace_path / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(src.resolve())
        
        # Create workspace config
        config = {
            "agent_type": agent_type,
            "workspace_path": str(workspace_path),
            "writable_paths": AGENT_MODULES[agent_type]["paths"],
            "read_only_paths": AGENT_MODULES[agent_type]["read_only"],
            "created_at": os.path.getmtime(workspace_path)
        }
        
        with open(workspace_path / ".workspace_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"Created workspace for {agent_type} agent at: {workspace_path}")
        return workspace_path
    
    def sync_changes(self, agent_type: str) -> Dict[str, List[str]]:
        """Sync changes from workspace back to main codebase."""
        workspace_path = self.workspaces_dir / f"{agent_type}_workspace"
        if not workspace_path.exists():
            raise ValueError(f"No workspace found for {agent_type}")
        
        changes = {"modified": [], "added": [], "deleted": []}
        
        # Check each writable path for changes
        for path in AGENT_MODULES[agent_type]["paths"]:
            workspace_file = workspace_path / path
            original_file = self.base_path / path
            
            if workspace_file.exists() and original_file.exists():
                # Compare files/directories
                if workspace_file.is_file():
                    if self._files_differ(workspace_file, original_file):
                        shutil.copy2(workspace_file, original_file)
                        changes["modified"].append(str(path))
                else:
                    # For directories, use rsync or similar
                    self._sync_directory(workspace_file, original_file, changes)
            elif workspace_file.exists() and not original_file.exists():
                # New file/directory
                if workspace_file.is_file():
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(workspace_file, original_file)
                else:
                    shutil.copytree(workspace_file, original_file)
                changes["added"].append(str(path))
            elif not workspace_file.exists() and original_file.exists():
                # Deleted file/directory
                if original_file.is_file():
                    original_file.unlink()
                else:
                    shutil.rmtree(original_file)
                changes["deleted"].append(str(path))
        
        return changes
    
    def validate_workspace(self, agent_type: str) -> Dict[str, any]:
        """Validate workspace integrity and permissions."""
        workspace_path = self.workspaces_dir / f"{agent_type}_workspace"
        if not workspace_path.exists():
            return {"valid": False, "error": "Workspace does not exist"}
        
        # Load config
        config_path = workspace_path / ".workspace_config.json"
        if not config_path.exists():
            return {"valid": False, "error": "Missing workspace config"}
        
        with open(config_path) as f:
            config = json.load(f)
        
        issues = []
        
        # Check writable paths exist and are writable
        for path in config["writable_paths"]:
            full_path = workspace_path / path
            if not full_path.exists():
                issues.append(f"Missing writable path: {path}")
            elif not os.access(full_path, os.W_OK):
                issues.append(f"Path not writable: {path}")
        
        # Check read-only paths are symlinks
        for path in config["read_only_paths"]:
            full_path = workspace_path / path
            if full_path.exists() and not full_path.is_symlink():
                issues.append(f"Read-only path is not a symlink: {path}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "workspace_age_hours": (time.time() - config["created_at"]) / 3600
        }
    
    def clean_workspace(self, agent_type: str):
        """Remove an agent's workspace."""
        workspace_path = self.workspaces_dir / f"{agent_type}_workspace"
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
            print(f"Removed workspace for {agent_type}")
    
    def list_workspaces(self) -> List[Dict]:
        """List all existing workspaces."""
        workspaces = []
        for workspace_dir in self.workspaces_dir.iterdir():
            if workspace_dir.is_dir() and workspace_dir.name.endswith("_workspace"):
                config_path = workspace_dir / ".workspace_config.json"
                if config_path.exists():
                    with open(config_path) as f:
                        config = json.load(f)
                    workspaces.append({
                        "agent_type": config["agent_type"],
                        "path": str(workspace_dir),
                        "age_hours": (time.time() - config["created_at"]) / 3600
                    })
        return workspaces
    
    def _files_differ(self, file1: Path, file2: Path) -> bool:
        """Check if two files differ."""
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            return f1.read() != f2.read()
    
    def _sync_directory(self, src: Path, dst: Path, changes: Dict):
        """Sync directory changes."""
        # Use rsync for efficient directory sync
        result = subprocess.run(
            ["rsync", "-av", "--delete", f"{src}/", f"{dst}/"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse rsync output to categorize changes
            for line in result.stdout.split('\n'):
                if line and not line.startswith('sending') and not line.startswith('sent'):
                    relative_path = str(src.relative_to(self.workspaces_dir / f"{src.parent.name}_workspace"))
                    if line.startswith('deleting'):
                        changes["deleted"].append(relative_path)
                    else:
                        changes["modified"].append(relative_path)


def main():
    """CLI for workspace isolation tool."""
    parser = argparse.ArgumentParser(description="Agent Workspace Isolation Tool")
    parser.add_argument("--base-path", default=".", help="Base path of the project")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create workspace
    create_parser = subparsers.add_parser("create", help="Create a workspace")
    create_parser.add_argument("agent_type", choices=list(AGENT_MODULES.keys()))
    
    # Sync changes
    sync_parser = subparsers.add_parser("sync", help="Sync changes back")
    sync_parser.add_argument("agent_type", choices=list(AGENT_MODULES.keys()))
    
    # Validate workspace
    validate_parser = subparsers.add_parser("validate", help="Validate workspace")
    validate_parser.add_argument("agent_type", choices=list(AGENT_MODULES.keys()))
    
    # Clean workspace
    clean_parser = subparsers.add_parser("clean", help="Remove workspace")
    clean_parser.add_argument("agent_type", choices=list(AGENT_MODULES.keys()))
    
    # List workspaces
    list_parser = subparsers.add_parser("list", help="List all workspaces")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    base_path = Path(args.base_path).resolve()
    isolation = WorkspaceIsolation(base_path)
    
    if args.command == "create":
        isolation.create_workspace(args.agent_type)
    elif args.command == "sync":
        changes = isolation.sync_changes(args.agent_type)
        print("Changes synced:")
        for change_type, files in changes.items():
            if files:
                print(f"  {change_type}: {len(files)} files")
                for f in files[:5]:  # Show first 5
                    print(f"    - {f}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
    elif args.command == "validate":
        result = isolation.validate_workspace(args.agent_type)
        print(f"Workspace valid: {result['valid']}")
        if result.get('issues'):
            print("Issues found:")
            for issue in result['issues']:
                print(f"  - {issue}")
        if 'workspace_age_hours' in result:
            print(f"Workspace age: {result['workspace_age_hours']:.1f} hours")
    elif args.command == "clean":
        isolation.clean_workspace(args.agent_type)
    elif args.command == "list":
        workspaces = isolation.list_workspaces()
        if workspaces:
            print("Active workspaces:")
            for ws in workspaces:
                print(f"  - {ws['agent_type']}: {ws['path']} (age: {ws['age_hours']:.1f} hours)")
        else:
            print("No active workspaces found")


if __name__ == "__main__":
    import time
    main()