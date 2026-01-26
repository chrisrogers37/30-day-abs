---
description: "Generate project context summary for sharing with Claude web/phone"
---

Generate a current state summary that can be shared with Claude web/phone sessions.

Include:

1. **Current Branch & Status**
   ```sh
   git branch --show-current
   git status --short
   ```

2. **Recent Commits** (last 5)
   ```sh
   git log --oneline -5
   ```

3. **Test Status**
   ```sh
   pytest --collect-only -q 2>/dev/null | tail -1
   ```

4. **Current Version** (from CHANGELOG.md)
   - Read the [Unreleased] section
   - Note any pending changes

5. **Output Format**

   Create a summary like:
   ```
   ## Project Status: 30 Day A/Bs

   **Branch**: feature/xyz
   **Last commit**: abc123 - Description
   **Tests**: 283 collected
   **Pending changes**: [list from git status]

   **Recent work**:
   - Item 1
   - Item 2

   **Context file**: .claude/PROJECT_CONTEXT.md
   ```

This summary helps continue work in a different Claude session.
