---
description: "Start the Streamlit app and review the UI in Chrome"
---

## Test the UI

1. **Start the Streamlit server** (if not already running):
   ```sh
   ./venv/bin/streamlit run ui/streamlit_app.py --server.headless true --server.port 8501 &
   ```

2. **Wait for startup** then verify it's running:
   ```sh
   sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
   ```

3. **Open in Chrome** using the browser automation tools:
   - Create a new tab with `tabs_create_mcp`
   - Navigate to `http://localhost:8501`
   - Take a screenshot to see the current state

4. **Test the user flow**:
   - Click "Generate New Scenario" to create a test scenario
   - Verify the scenario loads correctly
   - Check each step of the workflow is accessible
   - Look for UI bugs, layout issues, or broken interactions

5. **Report findings**:
   - Screenshots of any issues found
   - Description of bugs or UX problems
   - Suggestions for improvements

## What to Check

- [ ] App loads without errors
- [ ] "Generate New Scenario" works
- [ ] All 4 workflow steps are accessible
- [ ] Forms accept input correctly
- [ ] Feedback displays properly
- [ ] Mobile/responsive layout (resize window)
- [ ] No console errors (check browser dev tools)
