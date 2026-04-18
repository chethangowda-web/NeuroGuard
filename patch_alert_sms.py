"""
NeuroGuard — Alert Manager SMS Simulation Patch
Replaces backend-fetching alert dashboard with a fully self-contained
front-end SMS simulation engine. Backend calls for other modules are untouched.
"""

html_path = r'd:\NG\neuroguard (1).html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)
changes = []

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1: Replace Alert Manager HTML (view-alerts block)
# Original: loads phone nums from backend, shows "Backend unreachable"
# New:      standalone SMS routing table + local alert log
# ─────────────────────────────────────────────────────────────────────────────
OLD_HTML = '''        <div class="view" id="view-alerts">
          <div class="panel-row panel-row-2">
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Automated SMS · Server routing (read-only)</div>
                <span class="badge badge-ok">Auto SMS</span>
              </div>
              <p style="font-size:11px;color:var(--txt3);margin-bottom:10px;line-height:1.5">
                Phone numbers are loaded from the NeuroGuard backend database per server. SMS is sent by the server when
                status changes (Normal, At risk, Critical, Recovered). No manual entry.
              </p>
              <div id="alert-servers-dashboard" class="alert-dash-grid scrollable"
                style="max-height:340px;padding-right:4px">
                <div style="color:var(--txt3);font-size:12px;padding:20px 0;text-align:center;grid-column:1/-1">Connect
                  to the API to load server routing…</div>
              </div>
              <div style="margin-top:12px">
                <div style="font-size:10px;color:var(--txt3);font-family:var(--mono);margin-bottom:8px">STATUS
                  THRESHOLDS (backend)</div>
                <div style="font-size:11px;color:var(--txt2);display:flex;flex-direction:column;gap:4px">
                  <div style="display:flex;justify-content:space-between"><span><span
                        class="badge badge-ok">NORMAL</span></span><span style="font-family:var(--mono)">&lt; 30% fail
                      prob · within CPU/RAM/Disk limits</span></div>
                  <div style="display:flex;justify-content:space-between"><span><span class="badge badge-warn">AT
                        RISK</span></span><span style="font-family:var(--mono)">30–69% or elevated resources</span>
                  </div>
                  <div style="display:flex;justify-content:space-between"><span><span
                        class="badge badge-crit">CRITICAL</span></span><span style="font-family:var(--mono)">≥ 70% or
                      severe resource stress</span></div>
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Alert Manager Output</div>
              </div>
              <div id="alert-result" style="color:var(--txt3);font-size:12px;text-align:center;padding:30px 0">Backend
                link status will appear here.</div>
            </div>
          </div>
          <div class="panel-row panel-row-2">
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Recent alert log (from backend)</div>
                <button class="btn btn-sm btn-danger" onclick="clearAlerts()">Clear local view</button>
              </div>
              <div id="active-alerts-list">
                <div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">Loading alert history…
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Alert Distribution (24h)</div>
              </div>
              <div class="chart-wrap" style="height:140px"><canvas id="alertChart2"></canvas></div>
              <div style="margin-top:10px;font-size:11px;color:var(--txt2);display:flex;flex-direction:column;gap:4px">
                <div style="display:flex;justify-content:space-between"><span>Critical alerts</span><span
                    style="font-family:var(--mono);color:#FCA5A5" id="alert-crit-count">2</span></div>
                <div style="display:flex;justify-content:space-between"><span>Warnings</span><span
                    style="font-family:var(--mono);color:#FCD34D" id="alert-warn-count">1</span></div>
                <div style="display:flex;justify-content:space-between"><span>Deduplication saves</span><span
                    style="font-family:var(--mono);color:#34D399" id="alert-dedup-count">0</span></div>
              </div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title">Python Alert Manager Module</div>
              <button class="btn btn-sm" onclick="copyOutput('alert-python')">Copy Code</button>
            </div>
            <div class="output-block" id="alert-python" style="min-height:80px">
              # Loading alert manager module code...
              # Auto alert payloads will appear here after dispatch
            </div>
          </div>
        </div>'''

NEW_HTML = '''        <div class="view" id="view-alerts">
          <div class="panel-row panel-row-2">
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">SMS Routing Active</div>
                <span class="badge badge-ok" style="background:rgba(52,211,153,.15);color:#34D399;border:1px solid #34D39340">● Live Simulation</span>
              </div>
              <p style="font-size:11px;color:var(--txt3);margin-bottom:12px;line-height:1.6">
                Auto-assigned demo numbers per server. SMS is simulated locally — Pending → Sending → Delivered.
                Status changes trigger automatic routing. No backend fetch required.
              </p>
              <div id="alert-servers-dashboard" class="alert-dash-grid scrollable" style="max-height:340px;padding-right:4px">
                <div style="color:var(--txt3);font-size:12px;padding:20px 0;text-align:center;grid-column:1/-1">
                  <span class="live-dot"></span>&nbsp; Initializing SMS routing…
                </div>
              </div>
              <div style="margin-top:12px">
                <div style="font-size:10px;color:var(--txt3);font-family:var(--mono);margin-bottom:8px">STATUS THRESHOLDS</div>
                <div style="font-size:11px;color:var(--txt2);display:flex;flex-direction:column;gap:4px">
                  <div style="display:flex;justify-content:space-between"><span><span class="badge badge-ok">NORMAL</span></span><span style="font-family:var(--mono)">&lt; 30% fail prob — no SMS</span></div>
                  <div style="display:flex;justify-content:space-between"><span><span class="badge badge-warn">AT RISK</span></span><span style="font-family:var(--mono)">30–69% — Warning SMS sent</span></div>
                  <div style="display:flex;justify-content:space-between"><span><span class="badge badge-crit">CRITICAL</span></span><span style="font-family:var(--mono)">≥ 70% — Emergency SMS sent</span></div>
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Alert Manager Output</div>
              </div>
              <div id="alert-result" style="color:var(--txt3);font-size:12px;text-align:center;padding:30px 0">
                Awaiting first sensor update…
              </div>
            </div>
          </div>
          <div class="panel-row panel-row-2">
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Recent Alert Log</div>
                <button class="btn btn-sm btn-danger" onclick="clearAlerts()">Clear</button>
              </div>
              <div id="active-alerts-list">
                <div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">
                  <span class="live-dot"></span>&nbsp; Awaiting alerts…
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">Alert Distribution (24h)</div>
              </div>
              <div class="chart-wrap" style="height:140px"><canvas id="alertChart2"></canvas></div>
              <div style="margin-top:10px;font-size:11px;color:var(--txt2);display:flex;flex-direction:column;gap:4px">
                <div style="display:flex;justify-content:space-between"><span>Critical alerts</span><span style="font-family:var(--mono);color:#FCA5A5" id="alert-crit-count">0</span></div>
                <div style="display:flex;justify-content:space-between"><span>Warnings</span><span style="font-family:var(--mono);color:#FCD34D" id="alert-warn-count">0</span></div>
                <div style="display:flex;justify-content:space-between"><span>SMS delivered</span><span style="font-family:var(--mono);color:#34D399" id="alert-dedup-count">0</span></div>
              </div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title">SMS Dispatch Log</div>
              <button class="btn btn-sm" onclick="copyOutput('alert-python')">Copy</button>
            </div>
            <div class="output-block" id="alert-python" style="min-height:80px">
              # NeuroGuard SMS Simulation Engine
              # Auto-routes alerts to assigned +91 numbers
              # Dispatch log will appear here after first sensor update
            </div>
          </div>
        </div>'''

if OLD_HTML in content:
    content = content.replace(OLD_HTML, NEW_HTML)
    changes.append("PATCH 1: Replaced Alert Manager HTML with standalone SMS simulation UI")
else:
    changes.append("SKIP PATCH 1: HTML block not matched exactly")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2: Replace refreshAlertDashboard (backend fetch) with SMS sim renderer
# ─────────────────────────────────────────────────────────────────────────────
OLD_JS_DASH = '''    let isFetchingDash = false;
    async function refreshAlertDashboard() {
      if (isFetchingDash) return;
      const host = document.getElementById('alert-servers-dashboard');
      if (!host) return;
      isFetchingDash = true;
      const originalHtml = host.innerHTML;
      if (!host.innerHTML.includes('dash-row')) {
        host.innerHTML = '<div style="color:var(--txt3);padding:20px;text-align:center;grid-column:1/-1">Loading dashboard <span class="live-dot"></span></div>';
      }
      try {
        const r = await fetchWithTimeout(`${NEUROGUARD_API_BASE}/api/v1/servers/alert-dashboard`, { timeout: 8000 });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const rows = await r.json();
        if (!rows.length) {
          host.innerHTML = '<div style="color:var(--txt3);font-size:12px;padding:20px;text-align:center;grid-column:1/-1">No servers in the database yet. Start the API — it seeds CNC_01, CNC_02, PUMP_03, CONVEYOR_04.</div>';
          return;
        }
        host.innerHTML = rows.map((s) => {
          const smsBadge = s.sms_enabled
            ? '<span class="badge badge-ok">SMS ON</span>'
            : '<span class="badge badge-warn">SMS OFF</span>';
          const st = s.current_status || '—';
          const stBadge = st === 'CRITICAL' ? 'badge-crit' : st === 'AT_RISK' ? 'badge-warn' : 'badge-ok';
          const delivery = s.last_delivery_status || '—';
          const lastSms = s.last_sms_sent_at || '—';
          const lastM = s.last_metrics_at || '—';
          return `<div class="alert-dash-card">
        <div class="dash-row"><span class="dash-label">Server</span><span class="dash-val" style="font-weight:600;color:var(--txt)">${s.server_name}</span></div>
        <div class="dash-row"><span class="dash-label">Slug</span><span class="dash-val">${s.server_slug}</span></div>
        <div class="dash-row"><span class="dash-label">Status</span><span><span class="badge ${stBadge}">${st}</span></span></div>
        <div class="dash-row"><span class="dash-label">Assigned #</span><span class="dash-val">${s.assigned_phone_number}</span></div>
        <div class="dash-row"><span class="dash-label">SMS</span><span>${smsBadge}</span></div>
        <div class="dash-row"><span class="dash-label">Last SMS</span><span class="dash-val">${lastSms}</span></div>
        <div class="dash-row"><span class="dash-label">Delivery</span><span class="dash-val">${delivery}</span></div>
        <div class="dash-row"><span class="dash-label">Last metrics</span><span class="dash-val">${lastM}</span></div>
      </div>`;
        }).join('');
      } catch (e) {
        console.error("Dashboard error", e);
        host.innerHTML = `<div class="alert-item alert-warn" style="grid-column:1/-1;margin:0"><div class="alert-title">Backend unreachable</div><div class="alert-msg">${e.message}</div></div>`;
      } finally {
        isFetchingDash = false;
      }
    }'''

NEW_JS_DASH = '''    // ── SMS SIMULATION ENGINE ────────────────────────────────────
    // Generates stable demo phone numbers per server for this session.
    // No backend fetch — fully self-contained.

    const _SMS_PREFIXES = ['98', '97', '91', '99', '88', '76', '70', '63', '62', '60'];
    function _genPhone() {
      const p = _SMS_PREFIXES[Math.floor(Math.random() * _SMS_PREFIXES.length)];
      const rest = String(Math.floor(Math.random() * 90000000) + 10000000);
      return '+91 ' + p + rest;
    }

    // Stable number map (generated once per session per server)
    const _serverPhones = new Map();
    function _getPhone(serverName) {
      if (!_serverPhones.has(serverName)) _serverPhones.set(serverName, _genPhone());
      return _serverPhones.get(serverName);
    }

    // SMS log (in-memory, max 30 entries)
    const _smsLog = [];
    let _smsDelivered = 0;

    function _smsType(failProb) {
      if (failProb >= 70) return { type: 'CRITICAL', label: '🔴 Emergency SMS', cls: 'alert-crit' };
      if (failProb >= 30) return { type: 'AT_RISK', label: '🟡 Warning SMS', cls: 'alert-warn' };
      return { type: 'NORMAL', label: '✅ Recovery SMS', cls: 'alert-ok' };
    }

    // Simulate SMS dispatch: Pending → Sending → Delivered over ~3s
    function _simulateSmsDispatch(serverName, phone, failProb, onDone) {
      const { label, cls } = _smsType(failProb);
      const entry = {
        server: serverName, phone, label, cls,
        status: 'Pending', time: new Date().toLocaleTimeString()
      };
      _smsLog.unshift(entry);
      if (_smsLog.length > 30) _smsLog.pop();
      _renderSmsLog();

      setTimeout(() => {
        entry.status = 'Sending…';
        _renderSmsLog();
        setTimeout(() => {
          entry.status = 'Delivered ✓';
          _smsDelivered++;
          _renderSmsLog();
          if (onDone) onDone();
        }, 1500);
      }, 800);
    }

    function _renderSmsLog() {
      const list = document.getElementById('active-alerts-list');
      if (!list) return;
      if (!_smsLog.length) {
        list.innerHTML = '<div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">No alerts yet — awaiting sensor data…</div>';
        return;
      }
      list.innerHTML = _smsLog.slice(0, 30).map(e => `
        <div class="alert-item ${e.cls}" style="margin-bottom:6px">
          <div class="alert-title">${e.server} → ${e.phone}</div>
          <div class="alert-msg">${e.label}</div>
          <div class="alert-meta">${e.time} · ${e.status}</div>
        </div>`).join('');

      // Update counters
      const crits = _smsLog.filter(e => e.cls === 'alert-crit').length;
      const warns = _smsLog.filter(e => e.cls === 'alert-warn').length;
      const critEl = document.getElementById('alert-crit-count');
      const warnEl = document.getElementById('alert-warn-count');
      const dedupEl = document.getElementById('alert-dedup-count');
      if (critEl) critEl.textContent = crits;
      if (warnEl) warnEl.textContent = warns;
      if (dedupEl) dedupEl.textContent = _smsDelivered;
    }

    // Dedup guard: only send SMS when status actually changes
    const _lastSmsStatus = new Map();
    function _shouldSendSms(serverName, failProb) {
      const newType = failProb >= 70 ? 'CRITICAL' : failProb >= 30 ? 'AT_RISK' : 'NORMAL';
      if (_lastSmsStatus.get(serverName) === newType) return false;
      _lastSmsStatus.set(serverName, newType);
      return newType !== 'NORMAL'; // don't SMS on NORMAL
    }

    // Public API — called from prediction cycle
    function simulateSmsAlert(serverName, failProb) {
      if (!_shouldSendSms(serverName, failProb)) return;
      const phone = _getPhone(serverName);
      _simulateSmsDispatch(serverName, phone, failProb, () => {
        // Update alert-result panel
        const { label, cls } = _smsType(failProb);
        const resultEl = document.getElementById('alert-result');
        if (resultEl) {
          resultEl.innerHTML = `<div class="alert-item ${cls}">
            <div class="alert-title">${label} dispatched</div>
            <div class="alert-msg">${serverName} → ${phone}</div>
            <div class="alert-meta">${new Date().toLocaleTimeString()} · Delivered</div>
          </div>`;
        }
        const pyEl = document.getElementById('alert-python');
        if (pyEl) pyEl.textContent = JSON.stringify({
          server: serverName, phone, sms_type: _smsType(failProb).type,
          failure_probability: failProb, status: 'delivered', timestamp: new Date().toISOString()
        }, null, 2);
      });
    }

    function refreshAlertDashboard() {
      const host = document.getElementById('alert-servers-dashboard');
      if (!host) return;
      // Build card for each known server from live dataset
      const known = servers.length ? servers : [];
      if (!known.length) {
        host.innerHTML = '<div style="color:var(--txt3);font-size:12px;padding:20px 0;text-align:center;grid-column:1/-1"><span class="live-dot"></span>&nbsp; Awaiting dataset stream…</div>';
        return;
      }
      host.innerHTML = known.map(s => {
        const phone = _getPhone(s.name);
        const stBadge = s.status === 'crit' ? 'badge-crit' : s.status === 'warn' ? 'badge-warn' : 'badge-ok';
        const stLabel = s.status === 'crit' ? 'CRITICAL' : s.status === 'warn' ? 'AT RISK' : 'NORMAL';
        const lastEntry = _smsLog.find(e => e.server === s.name);
        const lastSms = lastEntry ? lastEntry.time + ' · ' + lastEntry.status : '—';
        const smsBadge = s.status !== 'ok'
          ? '<span class="badge badge-ok">SMS ON</span>'
          : '<span class="badge" style="background:rgba(100,116,139,.15);color:var(--txt3)">No SMS</span>';
        return `<div class="alert-dash-card">
          <div class="dash-row"><span class="dash-label">Server</span><span class="dash-val" style="font-weight:600;color:var(--txt)">${s.name}</span></div>
          <div class="dash-row"><span class="dash-label">Status</span><span><span class="badge ${stBadge}">${stLabel}</span></span></div>
          <div class="dash-row"><span class="dash-label">Assigned #</span><span class="dash-val" style="font-family:var(--mono)">${phone}</span></div>
          <div class="dash-row"><span class="dash-label">SMS</span><span>${smsBadge}</span></div>
          <div class="dash-row"><span class="dash-label">Last SMS</span><span class="dash-val">${lastSms}</span></div>
          <div class="dash-row"><span class="dash-label">Fail Prob</span><span class="dash-val" style="font-family:var(--mono);color:${s.failProb>=70?'#FCA5A5':s.failProb>=30?'#FCD34D':'#34D399'}">${s.failProb}%</span></div>
        </div>`;
      }).join('');
    }'''

if OLD_JS_DASH in content:
    content = content.replace(OLD_JS_DASH, NEW_JS_DASH)
    changes.append("PATCH 2: Replaced refreshAlertDashboard backend fetch with SMS simulation engine")
else:
    changes.append("SKIP PATCH 2: JS dash function not matched exactly")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3: Replace refreshAlertLogs (backend fetch) with _renderSmsLog call
# ─────────────────────────────────────────────────────────────────────────────
OLD_JS_LOGS = '''    let isFetchingLogs = false;
    async function refreshAlertLogs() {
      if (isFetchingLogs) return;
      const list = document.getElementById('active-alerts-list');
      if (!list) return;
      isFetchingLogs = true;
      if (!list.innerHTML.includes('alert-title')) {
        list.innerHTML = '<div style="color:var(--txt3);padding:20px;text-align:center">Loading logs <span class="live-dot"></span></div>';
      }
      try {
        const r = await fetchWithTimeout(`${NEUROGUARD_API_BASE}/api/v1/alert-logs?limit=30`, { timeout: 8000 });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const logs = await r.json();
        if (!logs.length) {
          list.innerHTML = '<div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">No alert log entries yet.</div>';
          return;
        }
        list.innerHTML = logs.map((log) => {
          const sev = log.to_status === 'CRITICAL' ? 'crit' : log.to_status === 'AT_RISK' ? 'warn' : 'ok';
          const ok = log.success ? 'logged ok' : 'failed';
          return `<div class="alert-item alert-${sev}">
        <div class="alert-title">${log.server_slug}: ${log.from_status || '∅'} → ${log.to_status}</div>
        <div class="alert-msg">${log.message}</div>
        <div class="alert-meta">${new Date(log.created_at).toLocaleString()} · ${ok}${log.twilio_sid ? ' · SID ' + log.twilio_sid : ''}${log.error_detail ? ' · ' + log.error_detail : ''}</div>
      </div>`;
        }).join('');
      } catch (e) {
        console.error("Logs error", e);
        list.innerHTML = `<div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">Could not load logs (${e.message})</div>`;
      } finally {
        isFetchingLogs = false;
      }
    }'''

NEW_JS_LOGS = '''    function refreshAlertLogs() {
      _renderSmsLog();
    }'''

if OLD_JS_LOGS in content:
    content = content.replace(OLD_JS_LOGS, NEW_JS_LOGS)
    changes.append("PATCH 3: Replaced refreshAlertLogs backend fetch with local SMS log render")
else:
    changes.append("SKIP PATCH 3: JS logs function not matched exactly")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 4: Replace runAlert (the backend POST function) with simulateSmsAlert call
# Keep it named runAlert so existing code paths that call triggerAlert->runAlert still work
# ─────────────────────────────────────────────────────────────────────────────
OLD_RUN_ALERT = '''    let _runAlertInFlight = false;
    async function runAlert(payload = {}) {
      if (_runAlertInFlight) return;
      _runAlertInFlight = true;
      const slug = payload.server || currentPredictServer || 'unknown';
      const prob = Number.isFinite(payload.failure_probability) ? payload.failure_probability : 0;
      const lm = payload.liveMetrics || { cpu: 0, ram: 0, disk: 0 };
      const serverName = payload.serverName || slug;
      const ingestBody = JSON.stringify({
        server_slug: String(slug).trim(),
        server_name: serverName,
        cpu_percent: Number(lm.cpu) || 0,
        memory_percent: Number(lm.ram) || 0,
        disk_percent: Number(lm.disk) || 0,
        failure_probability_percent: prob,
      });
      let res, data;
      try {
        try {
          res = await fetchWithTimeout(`${NEUROGUARD_API_BASE}/api/v1/metrics/ingest`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: ingestBody, timeout: 8000
          });
        } catch (_) {
          await new Promise(r => setTimeout(r, 1000));
          res = await fetchWithTimeout(`${NEUROGUARD_API_BASE}/api/v1/metrics/ingest`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: ingestBody, timeout: 8000
          });
        }
        data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(formatApiError(data.detail) || data.message || res.statusText || 'Ingest failed');
        }

        document.getElementById('alert-result').innerHTML = `
      <div class="alert-item alert-ok">
        <div class="alert-title">✓ Metrics synced to backend</div>
        <div class="alert-msg">Server <span style="font-family:var(--mono)">${data.server_slug}</span> · Status <span style="font-family:var(--mono)">${data.last_status || '—'}</span></div>
        <div class="alert-meta">Delivery: ${data.last_delivery_status || '—'} · SMS evaluated: ${data.sms_evaluated}</div>
      </div>`;

        document.getElementById('alert-python').textContent = JSON.stringify(data, null, 2);

        if (document.getElementById('view-alerts') && document.getElementById('view-alerts').classList.contains('active')) {
          refreshAlertDashboard();
          refreshAlertLogs();
        }
      } catch (e) {
        const resultEl = document.getElementById('alert-result');
        if (resultEl) resultEl.innerHTML = `<div class="alert-item alert-warn"><div class="alert-title">⚠ Backend sync</div><div class="alert-msg">${e.message}</div></div>`;
        const pyEl = document.getElementById('alert-python');
        if (pyEl) pyEl.textContent = JSON.stringify({ error: e.message, slug, prob }, null, 2);
      } finally {
        _runAlertInFlight = false;
      }
    }'''

NEW_RUN_ALERT = '''    // runAlert: now uses frontend SMS simulation (no backend fetch)
    async function runAlert(payload = {}) {
      try {
        const slug = payload.server || currentPredictServer || 'unknown';
        const prob = Number.isFinite(payload.failure_probability) ? payload.failure_probability : 0;
        simulateSmsAlert(slug, prob);
        refreshAlertDashboard();
      } catch (e) {
        console.error('runAlert error:', e);
      }
    }'''

if OLD_RUN_ALERT in content:
    content = content.replace(OLD_RUN_ALERT, NEW_RUN_ALERT)
    changes.append("PATCH 4: Replaced runAlert backend POST with simulateSmsAlert frontend call")
else:
    changes.append("SKIP PATCH 4: runAlert function not matched exactly")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 5: Fix clearAlerts to use local SMS log
# ─────────────────────────────────────────────────────────────────────────────
OLD_CLEAR = '''    function clearAlerts() {
      document.getElementById('active-alerts-list').innerHTML = '<div style="color:var(--txt3);font-size:12px;padding:16px 0;text-align:center">Local list cleared — refreshing from backend…</div>';
      setTimeout(() => refreshAlertLogs(), 400);
    }'''

NEW_CLEAR = '''    function clearAlerts() {
      _smsLog.length = 0;
      _smsDelivered = 0;
      _renderSmsLog();
      refreshAlertDashboard();
    }'''

if OLD_CLEAR in content:
    content = content.replace(OLD_CLEAR, NEW_CLEAR)
    changes.append("PATCH 5: clearAlerts now clears local SMS log instead of backend refetch")
else:
    changes.append("SKIP PATCH 5: clearAlerts not matched")

# ─────────────────────────────────────────────────────────────────────────────
# Write result
# ─────────────────────────────────────────────────────────────────────────────
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nPatched: {html_path}")
print(f"Size: {original_len} -> {len(content)} bytes ({len(content)-original_len:+d})")
print(f"\nResults ({len(changes)}):")
for c in changes:
    print(f"  {'OK' if not c.startswith('SKIP') else '!!'} {c}")

import shutil
shutil.copy2(html_path, r'd:\NG\NeuroGuard — AI Predictive Maintenance.html')
print("\nCopied to mirror file.")
