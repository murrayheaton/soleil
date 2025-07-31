# Claude Code Execution Instructions

## How to Execute PRPs

To execute a PRP with Claude Code, use this format:

```
Execute the PRP at PRPs/active/[filename].md

Make sure to:
1. Read ALL documentation files first (CLAUDE.md, PLANNING.md, etc.)
2. Create the appropriate feature branch before starting
3. Test locally before deploying
4. Use ./deploy-to-do.sh for deployment (not local deployment scripts)
5. Update all documentation after implementation
```

## Available PRPs (in priority order)

1. **CRITICAL - Profile Loading Fix**
   ```
   Execute the PRP at PRPs/active/01_fix_profile_loading_issue.md
   ```

2. **HIGH - Navigation and UI Updates**
   ```
   Execute the PRP at PRPs/active/02_navigation_ui_updates.md
   ```

3. **HIGH - Dashboard Implementation**
   ```
   Execute the PRP at PRPs/active/03_dashboard_implementation.md
   ```

## Important Notes

- Each PRP is self-contained and can be executed independently
- The PRPs include all production endpoints (https://solepower.live)
- Backend API is at https://solepower.live/api
- Deployment uses the IP 159.203.62.132
- Always create a feature branch for each PRP
- Test thoroughly before deploying to production

## Example Full Command

```
Execute the PRP at PRPs/active/01_fix_profile_loading_issue.md

Follow all instructions in the PRP exactly, including:
- Reading all documentation first
- Creating the feature branch
- Testing locally before deployment
- Using ./deploy-to-do.sh for deployment
- Updating documentation after completion
```