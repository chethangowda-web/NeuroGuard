"""
NeuroGuard Comprehensive Fix Script
Applies all required fixes without changing UI design, database, or working features.
"""

html_path = r'd:\NG\neuroguard (1).html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)
changes = []

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1: fetchLiveMetrics must NOT call stepDatasetPlayback (causes double-advance)
# ─────────────────────────────────────────────────────────────────────────────
OLD = """    async function fetchLiveMetrics() {
      if (datasetsLoaded) {
        stepDatasetPlayback();
      } else {
        refreshServers();
      }"""

NEW = """    async function fetchLiveMetrics() {
      try {
        if (!datasetsLoaded) {
          refreshServers();
        }
      } catch (_) {}"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 1: fetchLiveMetrics no longer double-steps dataset on every prediction call")
else:
    changes.append("SKIP FIX 1: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2: runAlert - add inflight lock + retry + fetchWithTimeout
# ─────────────────────────────────────────────────────────────────────────────
OLD = """    async function runAlert(payload = {}) {
      const slug = payload.server || currentPredictServer || 'unknown';
      const prob = Number.isFinite(payload.failure_probability) ? payload.failure_probability : 0;
      const lm = payload.liveMetrics || { cpu: 0, ram: 0, disk: 0 };
      const serverName = payload.serverName || slug;

      try {
        const res = await fetch(`${NEUROGUARD_API_BASE}/api/v1/metrics/ingest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            server_slug: String(slug).trim(),
            server_name: serverName,
            cpu_percent: Number(lm.cpu) || 0,
            memory_percent: Number(lm.ram) || 0,
            disk_percent: Number(lm.disk) || 0,
            failure_probability_percent: prob,
          }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(formatApiError(data.detail) || data.message || res.statusText || 'Ingest failed');
        }"""

NEW = """    let _runAlertInFlight = false;
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
        }"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 2: runAlert prevents concurrent requests + retries once on failure")
else:
    changes.append("SKIP FIX 2: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3: release _runAlertInFlight in finally block
# ─────────────────────────────────────────────────────────────────────────────
OLD = """      } catch (e) {
        document.getElementById('alert-result').innerHTML = `<div class="alert-item alert-warn"><div class="alert-title">⚠ Backend sync</div><div class="alert-msg">${e.message}</div></div>`;
        document.getElementById('alert-python').textContent = JSON.stringify({ error: e.message, slug, prob }, null, 2);
      }
    }"""

NEW = """      } catch (e) {
        const resultEl = document.getElementById('alert-result');
        if (resultEl) resultEl.innerHTML = `<div class="alert-item alert-warn"><div class="alert-title">⚠ Backend sync</div><div class="alert-msg">${e.message}</div></div>`;
        const pyEl = document.getElementById('alert-python');
        if (pyEl) pyEl.textContent = JSON.stringify({ error: e.message, slug, prob }, null, 2);
      } finally {
        _runAlertInFlight = false;
      }
    }"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 3: runAlert releases flight lock in finally block")
else:
    changes.append("SKIP FIX 3: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 4: stepDatasetPlayback triggers live cycle + auto-playbook generation
# ─────────────────────────────────────────────────────────────────────────────
OLD = """    function stepDatasetPlayback() {
      machineHistory.forEach((readings, machineId) => {
        const current = machinePointers.get(machineId) || 0;
        const next = readings.length ? (current + 1) % readings.length : 0;
        machinePointers.set(machineId, next);
      });
      applyDatasetSnapshot();
    }"""

NEW = """    function stepDatasetPlayback() {
      machineHistory.forEach((readings, machineId) => {
        const current = machinePointers.get(machineId) || 0;
        const next = readings.length ? (current + 1) % readings.length : 0;
        machinePointers.set(machineId, next);
      });
      applyDatasetSnapshot();
      _runLiveCycleAfterStep();
    }

    let _liveCycleRunning = false;
    async function _runLiveCycleAfterStep() {
      if (_liveCycleRunning) return;
      _liveCycleRunning = true;
      try {
        const liveMetrics = await fetchLiveMetrics();
        if (!liveMetrics) return;
        const prediction = runPrediction(liveMetrics);
        if (!prediction) return;
        currentPredictServer = liveMetrics.server;
        lastPredictMetrics = prediction;
        lastPredictInput = { cpu: liveMetrics.cpu, ram: liveMetrics.ram, disk: liveMetrics.disk, net: liveMetrics.net };
        predictionCount++;

        renderPredictionCards(prediction, liveMetrics);
        const rawEl = document.getElementById('predict-raw');
        if (rawEl) rawEl.textContent = JSON.stringify({ liveMetrics, prediction }, null, 2);
        const timeEl = document.getElementById('predict-time');
        if (timeEl) timeEl.textContent = new Date().toLocaleTimeString() + ' · live';

        buildShap(liveMetrics.cpu, liveMetrics.ram, liveMetrics.disk, liveMetrics.net);
        const explainEl = document.getElementById('explain-output');
        if (explainEl) explainEl.textContent = 'Live AI explanation: ' + prediction.server + ' risk is ' + prediction.failure_probability + '% (' + prediction.severity + '). Drivers: CPU ' + liveMetrics.cpu + '%, RAM ' + liveMetrics.ram + '%, Disk ' + liveMetrics.disk + '%, Log errors ' + liveMetrics.logErrors + '. Estimated TTF ' + prediction.time_to_failure + '.';

        _autoUpdateTwin(liveMetrics);

        if (prediction.failure_probability >= 30) {
          const jsonEvent = deriveJsonEvent(prediction.server, prediction);
          autoHeal(prediction, liveMetrics, jsonEvent);
          _autoGenerateTwinPlaybook(prediction, liveMetrics);
        }

        upsertServerFromMetrics(liveMetrics.server, liveMetrics.cpu, liveMetrics.ram, liveMetrics.disk, liveMetrics.net, prediction);
        updateAutoMonitoringPanel(liveMetrics, prediction);
        triggerAlert({ server: prediction.server, failure_probability: prediction.failure_probability, liveMetrics }).catch(() => {});
      } catch (e) {
        console.error('Live cycle error:', e);
      } finally {
        _liveCycleRunning = false;
      }
    }

    function _autoUpdateTwin(liveMetrics) {
      try {
        const cpuM = Math.max(1, Math.min(4, liveMetrics.cpu / 55)).toFixed(1);
        const memP = Math.max(30, Math.min(100, liveMetrics.ram));
        const diskS = Math.max(0, Math.min(100, liveMetrics.disk));
        const cpuEl = document.getElementById('cpu-mult');
        const memEl = document.getElementById('mem-press');
        const diskEl = document.getElementById('disk-sat');
        if (cpuEl && Math.abs(parseFloat(cpuEl.value) - parseFloat(cpuM)) > 0.3) cpuEl.value = cpuM;
        if (memEl && Math.abs(parseFloat(memEl.value) - memP) > 5) memEl.value = memP;
        if (diskEl && Math.abs(parseFloat(diskEl.value) - diskS) > 5) diskEl.value = diskS;
        updateSim();
      } catch (_) {}
    }

    let _lastPlaybookKey = '';
    function _autoGenerateTwinPlaybook(prediction, liveMetrics) {
      try {
        const key = prediction.server + '-' + prediction.severity + '-' + Math.round(prediction.failure_probability / 10);
        if (_lastPlaybookKey === key) return;
        _lastPlaybookKey = key;
        const cpu = liveMetrics.cpu, ram = liveMetrics.ram, disk = liveMetrics.disk, prob = prediction.failure_probability;
        const actions = [];
        if (cpu > 85) actions.push({ type: 'CRITICAL', icon: '🔴', title: 'Scale Kubernetes Pods', desc: 'CPU at ' + cpu + '% — horizontal pod autoscaler triggered' });
        if (ram > 80) actions.push({ type: 'WARN', icon: '🟡', title: 'Clear Application Cache', desc: 'RAM at ' + ram + '% — flush cache, clear temp files' });
        if (disk > 80) actions.push({ type: 'WARN', icon: '🟡', title: 'Disk Cleanup & Rotation', desc: 'Disk at ' + disk + '% — rotate logs, clean images' });
        if (prob > 70) actions.push({ type: 'CRITICAL', icon: '🔴', title: 'Enable Circuit Breaker', desc: 'High failure prob — enable circuit breaker, route to DR' });
        if (prob > 50) actions.push({ type: 'INFO', icon: '🔵', title: 'Alert On-Call Team', desc: 'Send SMS alert to registered numbers' });
        actions.push({ type: 'INFO', icon: '🔵', title: 'Update Monitoring Thresholds', desc: 'Tighten alert thresholds for the next 2 hours' });
        const bashScript = '#!/bin/bash\\nset -euo pipefail\\n# NeuroGuard Auto-Generated Remediation — ' + prediction.server + '\\n# Severity: ' + prediction.severity + ' | Fail Prob: ' + prob + '%\\necho "=== Starting remediation for ' + prediction.server + ' ==="\\n' +
          (cpu > 85 ? 'kubectl scale deployment ' + prediction.server + ' --replicas=+2 -n production\\n' : '') +
          (ram > 80 ? 'redis-cli FLUSHALL 2>/dev/null || true\\nfind /tmp -mtime +1 -delete\\n' : '') +
          (disk > 80 ? 'journalctl --vacuum-size=500M\\ndocker system prune -f\\n' : '') +
          'echo "=== Remediation complete ==="';
        const bashEl = document.getElementById('playbook-bash-content');
        if (bashEl && (bashEl.textContent.includes('will appear') || bashEl.textContent.trim() === '')) bashEl.textContent = bashScript;
        const actionsEl = document.getElementById('autoheal-actions');
        if (actionsEl) {
          actionsEl.innerHTML = '<div style="display:flex;flex-direction:column;gap:8px">' + actions.map((a, idx) =>
            '<div class="alert-item ' + (a.type === 'CRITICAL' ? 'alert-crit' : a.type === 'WARN' ? 'alert-warn' : 'alert-info') + '" style="margin-bottom:0"><div class="alert-title">' + (idx+1) + '. ' + a.icon + ' ' + a.title + '</div><div class="alert-msg">' + a.desc + '</div></div>').join('') + '</div>';
        }
      } catch (e) { console.error('Auto playbook error:', e); }
    }"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 4: stepDatasetPlayback triggers full live cycle + auto-playbook")
else:
    changes.append("SKIP FIX 4: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 5: startAutoMonitoring - simplify (dataset drives the cycle)
# ─────────────────────────────────────────────────────────────────────────────
OLD = """      const runCycle = async () => {
        const liveMetrics = await fetchLiveMetrics();
        if (!liveMetrics) {
          const connection = document.getElementById('auto-connection-status');
          if (connection) connection.textContent = 'WAITING FOR JSON STREAM';
          return;
        }
        const prediction = runPrediction(liveMetrics);
        currentPredictServer = liveMetrics.server;
        lastPredictMetrics = prediction;
        lastPredictInput = { cpu: liveMetrics.cpu, ram: liveMetrics.ram, disk: liveMetrics.disk, net: liveMetrics.net };
        predictionCount++;
        upsertServerFromMetrics(liveMetrics.server, liveMetrics.cpu, liveMetrics.ram, liveMetrics.disk, liveMetrics.net, prediction);
        buildShap(liveMetrics.cpu, liveMetrics.ram, liveMetrics.disk, liveMetrics.net);
        renderPredictionCards(prediction, liveMetrics);
        document.getElementById('predict-raw').textContent = JSON.stringify({ liveMetrics, prediction }, null, 2);
        document.getElementById('predict-time').textContent = `${new Date().toLocaleTimeString()} · auto`;
        updateAutoMonitoringPanel(liveMetrics, prediction);
        document.getElementById('explain-output').textContent = `Live AI explanation: ${prediction.server} risk is ${prediction.failure_probability}% (${prediction.severity}). Drivers: CPU ${liveMetrics.cpu}%, RAM ${liveMetrics.ram}%, Disk ${liveMetrics.disk}%, Log errors ${liveMetrics.logErrors}. Estimated TTF ${prediction.time_to_failure}.`;
        await triggerAlert({
          server: prediction.server,
          failure_probability: prediction.failure_probability,
          liveMetrics
        });
        if (prediction.failure_probability >= 30) {
          const jsonEvent = deriveJsonEvent(prediction.server, prediction);
          autoHeal(prediction, liveMetrics, jsonEvent);
        }
      };
      await runCycle();
      autoMonitoringIntervalId = setInterval(runCycle, 60000);"""

NEW = """      const runCycle = async () => {
        try {
          const liveMetrics = await fetchLiveMetrics();
          if (!liveMetrics) {
            const connection = document.getElementById('auto-connection-status');
            if (connection) connection.textContent = 'WAITING FOR JSON STREAM';
            return;
          }
          const pred = runPrediction(liveMetrics);
          if (pred) updateAutoMonitoringPanel(liveMetrics, pred);
        } catch (e) { console.error('Monitor cycle error:', e); }
      };
      await runCycle();
      autoMonitoringIntervalId = setInterval(runCycle, 30000);"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 5: startAutoMonitoring simplified — dataset interval drives the live cycle")
else:
    changes.append("SKIP FIX 5: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 6: Clock updates every second
# ─────────────────────────────────────────────────────────────────────────────
OLD = "    setInterval(updateClock, 60000);\n    updateClock();"
NEW = "    setInterval(updateClock, 1000);\n    updateClock();"

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 6: Clock updates every second")
else:
    changes.append("SKIP FIX 6: already fixed or not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 7: Alert refreshes only fire when alerts view is visible
# ─────────────────────────────────────────────────────────────────────────────
OLD = """        refreshAlertDashboard();
        refreshAlertLogs();
      } catch (e) {
        const resultEl = document.getElementById('alert-result');"""

NEW = """        if (document.getElementById('view-alerts') && document.getElementById('view-alerts').classList.contains('active')) {
          refreshAlertDashboard();
          refreshAlertLogs();
        }
      } catch (e) {
        const resultEl = document.getElementById('alert-result');"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 7: Alert refreshes only fire when alerts view is visible")
else:
    # try original (before FIX3 applied)
    OLD2 = """        refreshAlertDashboard();
        refreshAlertLogs();
      } catch (e) {
        document.getElementById('alert-result').innerHTML"""
    if OLD2 in content:
        changes.append("SKIP FIX 7 (alt): runAlert still had original catch - FIX3 may not have run")
    else:
        changes.append("SKIP FIX 7: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 8: API base auto-detect
# ─────────────────────────────────────────────────────────────────────────────
OLD = "    const NEUROGUARD_API_BASE = 'http://127.0.0.1:8001';"
NEW = "    const NEUROGUARD_API_BASE = (window.location.hostname === '127.0.0.1' && window.location.port !== '5500' && window.location.port !== '3000') ? '' : 'http://127.0.0.1:8001';"

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 8: API base auto-detects same-origin vs absolute URL")
else:
    changes.append("SKIP FIX 8: already patched or not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 9: Remove json-node slug from runAutoHeal
# ─────────────────────────────────────────────────────────────────────────────
OLD = "      const server = currentPredictServer || 'json-node';"
NEW = "      const server = currentPredictServer || (servers.length ? servers[0].name : 'CNC_01');"

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 9: runAutoHeal no longer defaults to 'json-node'")
else:
    changes.append("SKIP FIX 9: not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 10: Remove json-node from runAutoHealFromTwin
# ─────────────────────────────────────────────────────────────────────────────
OLD = "      const inferredServer = servers.length ? servers.reduce((a, b) => (a.failProb > b.failProb ? a : b)).name : 'json-node';"
NEW = "      const inferredServer = servers.length ? servers.reduce((a, b) => (a.failProb > b.failProb ? a : b)).name : 'CNC_01';"

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 10: runAutoHealFromTwin fallback is now CNC_01")
else:
    changes.append("SKIP FIX 10: not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 11: Remove json-node from digital twin
# ─────────────────────────────────────────────────────────────────────────────
OLD = '      const twinServer = servers.length ? servers.reduce((a, b) => (a.failProb > b.failProb ? a : b)).name : "json-node";'
NEW = '      const twinServer = servers.length ? servers.reduce((a, b) => (a.failProb > b.failProb ? a : b)).name : "CNC_01";'

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 11: Digital twin fallback server is now CNC_01")
else:
    changes.append("SKIP FIX 11: not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 12: Remove manual-input slug from runPredict
# ─────────────────────────────────────────────────────────────────────────────
OLD = "          server: currentPredictServer || 'manual-input',"
NEW = "          server: currentPredictServer || (servers.length ? servers[0].name : 'CNC_01'),"

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 12: runPredict no longer sends 'manual-input' to backend")
else:
    changes.append("SKIP FIX 12: not found")

# ─────────────────────────────────────────────────────────────────────────────
# FIX 13: Digital Twin auto-generates playbook on updateSim call
# ─────────────────────────────────────────────────────────────────────────────
OLD = "      // Auto-trigger auto-heal button highlight if high risk\n      const btn = document.getElementById('autoheal-from-twin-btn');"
NEW = """      // Auto-generate playbook inline when risk >= 30
      if (failProb >= 30 && lastTwinMetrics) {
        const synMetrics = { cpu: Math.min(100, Math.round(cpuM * 55)), ram: memP, disk: diskS, net: netL,
          server: twinServer, temperature: 70, logErrors: failProb > 70 ? 3 : 0, logs: '', timestamp: new Date().toISOString() };
        const synPred = { server: twinServer, failure_probability: failProb,
          severity: failProb >= 70 ? 'CRITICAL' : 'WARNING',
          health_score: health, time_to_failure: ttf + 'h',
          risk_factors: { cpu_risk: cpuM > 2.5 ? 'HIGH' : 'MEDIUM', ram_risk: memP > 70 ? 'HIGH' : 'LOW',
            disk_risk: diskS > 60 ? 'HIGH' : 'LOW', net_risk: 'LOW', log_anomalies: 'NONE' }};
        _autoGenerateTwinPlaybook(synPred, synMetrics);
      }
      const btn = document.getElementById('autoheal-from-twin-btn');"""

if OLD in content:
    content = content.replace(OLD, NEW)
    changes.append("FIX 13: Digital Twin auto-generates playbook inline on each sim update")
else:
    changes.append("SKIP FIX 13: pattern not found")

# ─────────────────────────────────────────────────────────────────────────────
# Write file
# ─────────────────────────────────────────────────────────────────────────────
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nPatched {html_path}")
print(f"Size: {original_len} -> {len(content)} bytes ({len(content) - original_len:+d})")
print(f"\nChanges applied ({len(changes)}):")
for c in changes:
    print(f"  {'OK' if not c.startswith('SKIP') else 'SKIP'} {c}")

import shutil
dest = r'd:\NG\NeuroGuard — AI Predictive Maintenance.html'
shutil.copy2(html_path, dest)
print(f"\nCopied to: {dest}")
