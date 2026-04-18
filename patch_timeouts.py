import re

def patch_timeouts(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add generic fetch timeout logic
        timeout_fn = """
    // Timeout wrapper to prevent stuck fetches
    async function fetchWithTimeout(resource, options = {}) {
      const { timeout = 5000 } = options;
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeout);
      const response = await fetch(resource, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(id);
      return response;
    }
"""
        
        # Inject the timeout wrapper if not exists
        if "fetchWithTimeout" not in content:
            # Place it near formatting functions
            content = content.replace("function formatApiError(detail) {", timeout_fn + "\n    function formatApiError(detail) {")

        old_fetch_dash = "const r = await fetch(`${NEUROGUARD_API_BASE}/api/v1/servers/alert-dashboard`);"
        new_fetch_dash = "const r = await fetchWithTimeout(`${NEUROGUARD_API_BASE}/api/v1/servers/alert-dashboard`, { timeout: 8000 });"
        content = content.replace(old_fetch_dash, new_fetch_dash)

        old_fetch_logs = "const r = await fetch(`${NEUROGUARD_API_BASE}/api/v1/alert-logs?limit=30`);"
        new_fetch_logs = "const r = await fetchWithTimeout(`${NEUROGUARD_API_BASE}/api/v1/alert-logs?limit=30`, { timeout: 8000 });"
        content = content.replace(old_fetch_logs, new_fetch_logs)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched timeouts in {file_path}")
    except Exception as e:
        print(f"Error {file_path}: {e}")

patch_timeouts(r'd:\NG\neuroguard (1).html')
patch_timeouts(r'd:\NG\NeuroGuard — AI Predictive Maintenance.html')
