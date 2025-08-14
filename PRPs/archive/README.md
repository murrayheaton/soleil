# Active PRPs Directory

This directory contains PRPs (Project Requirement Prompts) that are ready to be executed.

**Current Status**: No active PRPs

PRPs will be placed here externally when work is needed. Claude Code should:
1. Check this directory at the start of each session
2. Execute any PRPs found here
3. Move completed PRPs to `../archive/`

## Workflow Reminder

```bash
# Check for active PRPs
ls *.md

# If PRPs exist, execute them following CLAUDE.md rules
# When complete, archive them:
mv completed-prp.md ../archive/
git add ../
git commit -m "chore: archive completed PRP [name]"
```