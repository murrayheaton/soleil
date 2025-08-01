# INITIAL.md - Claude Code Entry Point

## 🚀 START HERE - Read This First!

You are Claude Code operating in a development container. This file provides essential context and directs you to the proper workflow.

## 1. Verify Your Location

```bash
# ALWAYS run this first:
pwd
# Expected: /Users/murrayheaton/Documents/LocalCode/DevEnv/soleil
```

If not in the correct directory:
```bash
cd /Users/murrayheaton/Documents/LocalCode/DevEnv/soleil
```

## 2. Read Core Documentation

Before executing any PRPs, you MUST read these files in order:

1. **CLAUDE.md** - Contains all rules for:
   - DevContainer working directory restrictions
   - PRP execution workflow
   - Code standards and conventions
   - Documentation requirements

2. **PLANNING.md** - Project architecture and technical decisions

3. **PRODUCT_VISION.md** - What SOLEil is and current feature state

## 3. Check for Active PRPs

```bash
# List any active PRPs
ls PRPs/active/
```

If PRPs exist in `PRPs/active/`:
1. Read the PRP completely
2. Follow all Pre-Implementation Requirements
3. Execute tasks in order
4. Run validation tests
5. Archive when complete

## 4. Project Context

**Project**: SOLEil (Sole Power Live)  
**Description**: Band management platform with Google Workspace integration  
**Production**: https://solepower.live  
**Repository**: Private GitHub repo (murrayheaton/soleil)  

**Current State**:
- ✅ Authentication consolidated
- ✅ Repository privatized
- ✅ Core platform functional
- 🔄 Ready for new features via PRPs

## 5. Working Directory Rules Summary

- ✅ **ALLOWED**: All operations within `/DevEnv/soleil/`
- 🔍 **READ ONLY**: `/DevEnv/template-generator/` (for reference)
- ❌ **FORBIDDEN**: All other directories

## 6. No Active PRPs?

If `PRPs/active/` is empty:
- Report "No active PRPs found"
- Wait for user to provide PRPs
- DO NOT generate PRPs (they come from external sources)

## Remember

> Every session starts here at INITIAL.md  
> Read CLAUDE.md before any work  
> Stay within the soleil directory  
> Execute PRPs from active folder only  
> Archive completed work properly

---

**Now proceed to read CLAUDE.md for detailed rules and workflows.**