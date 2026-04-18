import re

def fix_frontend(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix dataset interval
    content = content.replace("datasetIntervalId = setInterval(stepDatasetPlayback, 1000);", 
                              "datasetIntervalId = setInterval(stepDatasetPlayback, 10000);")

    # Split alert intervals & add flags/spinners
    old_alert_init = """      if (v === 'alerts') {
        refreshAlertDashboard();
        refreshAlertLogs();
        if (!alertDashboardTimer) {
          alertDashboardTimer = setInterval(() => {
            refreshAlertDashboard();
            refreshAlertLogs();
          }, 60000);
        }
      }"""
    
    new_alert_init = """      if (v === 'alerts') {
        refreshAlertDashboard();
        refreshAlertLogs();
        if (!window._alertDashTimer) {
          window._alertDashTimer = setInterval(refreshAlertDashboard, 30000);
          window._alertLogsTimer = setInterval(refreshAlertLogs, 60000);
        }
      }"""
    content = content.replace(old_alert_init, new_alert_init)

    # Add try/catch and loading state to refreshAlertDashboard
    old_dash = """    async function refreshAlertDashboard() {
      const host = document.getElementById('alert-servers-dashboard');
      if (!host) return;
      try {"""
    
    new_dash = """    let isFetchingDash = false;
    async function refreshAlertDashboard() {
      if (isFetchingDash) return;
      const host = document.getElementById('alert-servers-dashboard');
      if (!host) return;
      isFetchingDash = true;
      const originalHtml = host.innerHTML;
      if (!host.innerHTML.includes('dash-row')) {
        host.innerHTML = '<div style="color:var(--txt3);padding:20px;text-align:center;grid-column:1/-1">Loading dashboard <span class="live-dot"></span></div>';
      }
      try {"""
    content = content.replace(old_dash, new_dash)

    old_dash_end = """        }).join('');
      } catch (e) {
        host.innerHTML = `<div class="alert-item alert-warn" style="grid-column:1/-1;margin:0"><div class="alert-title">Backend unreachable</div><div class="alert-msg">${e.message}. From repo root run: <span style="font-family:var(--mono)">uvicorn backend.app:app --reload</span></div></div>`;
      }
    }"""
    
    new_dash_end = """        }).join('');
      } catch (e) {
        console.error("Dashboard error", e);
        host.innerHTML = `<div class="alert-item alert-warn" style="grid-column:1/-1;margin:0"><div class="alert-title">Backend unreachable</div><div class="alert-msg">${e.message}</div></div>`;
      } finally {
        isFetchingDash = false;
      }
    }"""
    content = content.replace(old_dash_end, new_dash_end)


    # Add try/catch and loading state to refreshAlertLogs
    old_logs = """    async function refreshAlertLogs() {
      const list = document.getElementById('active-alerts-list');
      if (!list) return;
      try {"""
    
    new_logs = """    let isFetchingLogs = false;
    async function refreshAlertLogs() {
      if (isFetchingLogs) return;
      const list = document.getElementById('active-alerts-list');
      if (!list) return;
      isFetchingLogs = true;
      if (!list.innerHTML.includes('alert-title')) {
        list.innerHTML = '<div style="color:var(--txt3);padding:20px;text-align:center">Loading logs <span class="live-dot"></span></div>';
      }
      try {"""
    content = content.replace(old_logs, new_logs)

    old_logs_end = """        }).join('');
      } catch (e) {
        list.innerHTML = `<div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">Could not load logs (${e.message})</div>`;
      }
    }"""
    
    new_logs_end = """        }).join('');
      } catch (e) {
        console.error("Logs error", e);
        list.innerHTML = `<div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">Could not load logs (${e.message})</div>`;
      } finally {
        isFetchingLogs = false;
      }
    }"""
    content = content.replace(old_logs_end, new_logs_end)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {file_path}")

fix_frontend(r'd:\NG\neuroguard (1).html')
fix_frontend(r'd:\NG\NeuroGuard — AI Predictive Maintenance.html')
