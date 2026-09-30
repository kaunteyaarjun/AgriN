/**
 * AgriN — Shared Navigation, Neumorphism UI & System Runtime
 * Injected into every Stitch code.html page to provide:
 * 1. Neumorphic Soft UI Design System (loaded from neumorphism.css)
 * 2. Persistent Database connectivity (agrin-db.js)
 * 3. Gemini Vision AI Disease Diagnostic Scanner (gemini-disease-ai.js)
 * 4. Apple Maps MapKit JS Library integration (apple-maps.js)
 * 5. Neumorphic floating dock with live Database stats, Gemini scanner modal, and Apple Maps
 * 6. Working inter-page navigation & voice advisories
 */
(function() {
  'use strict';

  // ── Load Dependencies ──────────────────────────────────────
  function ensureDependency(tag, srcOrHref, isCss) {
    if (isCss) {
      if (!document.querySelector(`link[href*="${srcOrHref}"]`)) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = srcOrHref;
        document.head.appendChild(link);
      }
    } else {
      if (!document.querySelector(`script[src*="${srcOrHref}"]`)) {
        const script = document.createElement('script');
        script.src = srcOrHref;
        document.head.appendChild(script);
      }
    }
  }

  // Inject Neumorphic CSS and core engines
  ensureDependency('link', '/stitch/neumorphism.css', true);
  ensureDependency('script', '/stitch/agrin-db.js', false);
  ensureDependency('script', '/stitch/gemini-disease-ai.js', false);
  ensureDependency('script', '/stitch/apple-maps.js', false);

  // Apply neumorphic theme to body
  document.body.classList.add('neo-theme');

  // ── Route Map ──────────────────────────────────────────────
  const ROUTE_MAP = {
    'plots':                    '/stitch/home_farm_digital_twin/code.html',
    'health':                   '/stitch/home_farm_digital_twin/code.html',
    'advisories':               '/stitch/offline_mode_data_sync/code.html',
    'scan-ai':                  '/stitch/crop_disease_doctor/code.html',
    'scan':                     '/stitch/crop_disease_doctor/code.html',
    'what-if':                  '/stitch/what_if_simulator/code.html',
    'whatif':                   '/stitch/what_if_simulator/code.html',
    'sync':                     '/stitch/offline_mode_data_sync/code.html',
    'offline':                  '/stitch/offline_mode_data_sync/code.html',
    'profile-settings':         '/stitch/home_farm_digital_twin/code.html',
    'geospatial-command':       '/stitch/geospatial_command_triage_drawer/code.html',
    'geospatial':               '/stitch/geospatial_command_triage_drawer/code.html',
    'disease-triage-queue':     '/stitch/disease_triage_queue/code.html',
    'triage':                   '/stitch/disease_triage_queue/code.html',
    'farmer-plot-registry':     '/stitch/farmer_plot_management_directory/code.html',
    'registry':                 '/stitch/farmer_plot_management_directory/code.html',
    'telemetry-weather-stations':'/stitch/telemetry_weather_stations/code.html',
    'weather':                  '/stitch/telemetry_weather_stations/code.html',
    'api-integration-architecture':'/stitch/backend_api_integration_architecture/code.html',
    'api':                      '/stitch/backend_api_integration_architecture/code.html'
  };

  // ── Neumorphic Toast System (Matches Styleguide Pill Alerts) ─
  function showToast(message, type) {
    type = type || 'info';
    const alertConfig = {
      success: { bg: '#D4F4E4', border: '#85F8C4', text: '#065F46', icon: '✅' },
      warn:    { bg: '#FEF3C7', border: '#FCD34D', text: '#92400E', icon: '⚠️' },
      info:    { bg: '#EEF2F6', border: '#98DECB', text: '#0F172A', icon: 'ℹ️' },
      error:   { bg: '#FEE2E2', border: '#FCA5A5', text: '#991B1B', icon: '❌' }
    };
    const c = alertConfig[type] || alertConfig.info;
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:99999;' +
      'padding:12px 24px;border-radius:9999px;font-size:14px;font-weight:600;font-family:Inter,system-ui,sans-serif;' +
      'max-width:90vw;box-shadow:6px 6px 16px rgba(166,180,200,0.45),-6px -6px 16px rgba(255,255,255,0.95);' +
      'border:1.5px solid ' + c.border + ';background:' + c.bg + ';color:' + c.text + ';' +
      'display:flex;align-items:center;gap:10px;opacity:0;transition:opacity 0.25s ease,transform 0.25s ease;' +
      'transform:translateX(-50%) translateY(-10px);';
    toast.innerHTML = '<span style="font-size:18px;flex-shrink:0">' + c.icon + '</span><span>' + message + '</span>';
    document.body.appendChild(toast);
    requestAnimationFrame(function() {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(-50%) translateY(0)';
    });
    setTimeout(function() {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(-50%) translateY(-10px)';
      setTimeout(function() { toast.remove(); }, 300);
    }, 3500);
  }
  window.showAgriToast = showToast;

  // ── Voice / TTS ────────────────────────────────────────────
  window.speakAgriVoice = function(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      var utter = new SpeechSynthesisUtterance(text);
      utter.rate = 0.94;
      utter.pitch = 1.02;
      utter.lang = 'en-IN';
      window.speechSynthesis.speak(utter);
      showToast('🔊 Speaking: ' + text.slice(0, 48) + '...', 'info');
    } else {
      showToast('Voice: ' + text.slice(0, 60) + '...', 'info');
    }
  };

  // ── Neumorphic Floating Action Dock ────────────────────────
  function createNeumorphicDock() {
    if (document.getElementById('agrin-neo-dock')) return;

    const dock = document.createElement('div');
    dock.id = 'agrin-neo-dock';
    dock.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:99990;' +
      'display:flex;align-items:center;gap:10px;padding:8px 16px;border-radius:9999px;' +
      'background:rgba(238,242,246,0.92);backdrop-filter:blur(16px);' +
      'box-shadow:8px 8px 20px rgba(166,180,200,0.5), -8px -8px 20px rgba(255,255,255,0.95);' +
      'border:1px solid rgba(255,255,255,0.8);transition:all 0.25s ease;';

    dock.innerHTML = `
      <!-- Back to Portal Home -->
      <a href="/" title="Portal Hub" style="width:42px;height:42px;border-radius:50%;background:#EEF2F6;box-shadow:4px 4px 10px rgba(166,180,200,0.4),-4px -4px 10px rgba(255,255,255,0.9);display:flex;align-items:center;justify-content:center;color:#064E3B;text-decoration:none;transition:transform 0.15s ease;">
        <span style="font-size:18px;">🏠</span>
      </a>

      <!-- Quick Gemini Vision Disease Scanner -->
      <button id="dock-gemini-btn" title="Scan Disease with Gemini API" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border-radius:9999px;border:none;background:linear-gradient(135deg,#a8eed9 0%,#82deb0 100%);box-shadow:4px 4px 12px rgba(130,222,176,0.5),-4px -4px 12px rgba(255,255,255,0.9);color:#064E3B;font-weight:700;font-size:13px;cursor:pointer;font-family:inherit;">
        <span style="font-size:16px;">🔬</span>
        <span>Gemini AI Scan</span>
      </button>

      <!-- Apple Maps Quick View -->
      <a href="/stitch/geospatial_command_triage_drawer/code.html" title="Apple Maps GIS Command" style="display:flex;align-items:center;gap:6px;padding:8px 16px;border-radius:9999px;border:none;background:#EEF2F6;box-shadow:4px 4px 10px rgba(166,180,200,0.4),-4px -4px 10px rgba(255,255,255,0.9);color:#1E293B;font-weight:600;font-size:13px;text-decoration:none;cursor:pointer;">
        <span style="font-size:15px;"></span>
        <span>Apple Maps</span>
      </a>

      <!-- Database Inspector & Live Status -->
      <button id="dock-db-btn" title="Inspect Integrated Database" style="display:flex;align-items:center;gap:6px;padding:8px 14px;border-radius:9999px;border:none;background:#EEF2F6;box-shadow:4px 4px 10px rgba(166,180,200,0.4),-4px -4px 10px rgba(255,255,255,0.9);color:#0F766E;font-weight:600;font-size:12px;cursor:pointer;font-family:inherit;">
        <span style="width:8px;height:8px;border-radius:50%;background:#10B981;box-shadow:0 0 8px #10B981;display:inline-block;"></span>
        <span id="dock-db-label">Database Sync</span>
      </button>
    `;

    document.body.appendChild(dock);

    // Wire Gemini AI Modal Trigger
    const geminiBtn = document.getElementById('dock-gemini-btn');
    if (geminiBtn) {
      geminiBtn.addEventListener('click', () => {
        openGeminiScannerModal();
      });
    }

    // Wire Database Modal Trigger
    const dbBtn = document.getElementById('dock-db-btn');
    if (dbBtn) {
      dbBtn.addEventListener('click', () => {
        openDatabaseInspectorModal();
      });
    }
  }

  // ── Gemini AI Disease Diagnostic Modal ────────────────────
  function openGeminiScannerModal() {
    let modal = document.getElementById('agrin-gemini-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'agrin-gemini-modal';
      modal.style.cssText = 'position:fixed;inset:0;z-index:99995;background:rgba(15,23,42,0.6);' +
        'backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;padding:16px;';
      document.body.appendChild(modal);
    }

    const currentKey = localStorage.getItem('gemini_api_key') || '';
    const samples = window.GeminiDiseaseAI ? window.GeminiDiseaseAI.SAMPLE_LIBRARY : [];

    modal.innerHTML = `
      <div style="background:#EEF2F6;border-radius:24px;width:100%;max-width:640px;max-height:90vh;overflow-y:auto;padding:24px;
        box-shadow:16px 16px 36px rgba(166,180,200,0.6), -16px -16px 36px rgba(255,255,255,0.95);border:1px solid rgba(255,255,255,0.8);position:relative;font-family:Inter,system-ui,sans-serif;">
        
        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:between;margin-bottom:18px;">
          <div style="display:flex;align-items:center;gap:12px;flex:1;">
            <div style="width:48px;height:48px;border-radius:16px;background:#98DECB;box-shadow:4px 4px 10px rgba(140,215,195,0.5),-4px -4px 10px rgba(255,255,255,0.9);display:flex;align-items:center;justify-content:center;font-size:24px;">🔬</div>
            <div>
              <h2 style="font-size:18px;font-weight:800;color:#064E3B;margin:0;">Gemini AI Plant Disease Doctor</h2>
              <p style="font-size:12px;color:#64748B;margin:2px 0 0 0;">Multimodal Vision Diagnostic &amp; Prescription Engine</p>
            </div>
          </div>
          <button id="close-gemini-modal" style="width:36px;height:36px;border-radius:50%;border:none;background:#EEF2F6;box-shadow:3px 3px 8px rgba(166,180,200,0.4),-3px -3px 8px rgba(255,255,255,0.9);font-size:16px;font-weight:bold;cursor:pointer;color:#64748B;">✕</button>
        </div>

        <!-- Gemini API Key Inset Input -->
        <div style="background:#E8ECEF;padding:12px 16px;border-radius:16px;box-shadow:inset 3px 3px 6px rgba(166,180,200,0.4),inset -3px -3px 6px #fff;margin-bottom:16px;display:flex;align-items:center;gap:10px;">
          <span style="font-size:14px;">🔑</span>
          <input id="modal-gemini-key" type="password" placeholder="Enter Google Gemini API Key (Optional — instant botanical engine active)" value="${currentKey}" style="flex:1;background:transparent;border:none;outline:none;font-size:13px;color:#1E293B;">
          <button id="save-gemini-key" style="padding:6px 14px;border-radius:9999px;border:none;background:#98DECB;color:#064E3B;font-weight:700;font-size:11px;cursor:pointer;">Save Key</button>
        </div>

        <!-- Sample Leaf Selector -->
        <div style="margin-bottom:16px;">
          <label style="font-size:12px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:8px;">Choose Field Specimen to Analyze:</label>
          <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;">
            ${samples.map((s, idx) => `
              <div class="sample-leaf-card ${idx === 0 ? 'selected' : ''}" data-sample-id="${s.id}" style="padding:10px;border-radius:14px;background:#EEF2F6;box-shadow:4px 4px 10px rgba(166,180,200,0.35),-4px -4px 10px rgba(255,255,255,0.9);border:${idx === 0 ? '2px solid #00CFCC' : '1px solid rgba(255,255,255,0.7)'};cursor:pointer;display:flex;gap:10px;align-items:center;">
                <img src="${s.imageUrl}" style="width:48px;height:48px;border-radius:10px;object-cover:cover;box-shadow:inset 2px 2px 4px rgba(0,0,0,0.2);">
                <div style="flex:1;min-width:0;">
                  <div style="font-size:12px;font-weight:700;color:#1E293B;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${s.name}</div>
                  <div style="font-size:11px;color:#64748B;">${s.pathogen_type} • ${s.severity}</div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Trigger Button -->
        <button id="run-gemini-inference" style="width:100%;padding:14px;border-radius:9999px;border:none;background:linear-gradient(135deg,#a8eed9 0%,#82deb0 100%);box-shadow:6px 6px 16px rgba(130,222,176,0.5),-6px -6px 16px #fff;color:#064E3B;font-weight:800;font-size:15px;cursor:pointer;margin-bottom:16px;transition:transform 0.15s ease;">
          ⚡ Run Gemini Vision AI Diagnosis
        </button>

        <!-- Result Container -->
        <div id="gemini-result-view" style="display:none;background:#E8ECEF;box-shadow:inset 4px 4px 10px rgba(166,180,200,0.4),inset -4px -4px 10px #fff;border-radius:18px;padding:16px;">
          <!-- Dynamically populated -->
        </div>
      </div>
    `;

    modal.style.display = 'flex';

    // Close button
    document.getElementById('close-gemini-modal').onclick = () => { modal.style.display = 'none'; };

    // Save key
    document.getElementById('save-gemini-key').onclick = () => {
      const keyVal = document.getElementById('modal-gemini-key').value.trim();
      if (window.GeminiDiseaseAI) window.GeminiDiseaseAI.setApiKey(keyVal);
      showToast('Gemini API key saved to local database!', 'success');
    };

    // Selection
    let selectedSampleId = samples[0]?.id;
    modal.querySelectorAll('.sample-leaf-card').forEach(card => {
      card.onclick = () => {
        modal.querySelectorAll('.sample-leaf-card').forEach(c => c.style.border = '1px solid rgba(255,255,255,0.7)');
        card.style.border = '2px solid #00CFCC';
        selectedSampleId = card.getAttribute('data-sample-id');
      };
    });

    // Run inference
    const runBtn = document.getElementById('run-gemini-inference');
    runBtn.onclick = async () => {
      runBtn.innerText = '⏳ Gemini Vision Analyzing Lesion Structure...';
      runBtn.style.opacity = '0.7';

      try {
        const sample = samples.find(s => s.id === selectedSampleId) || samples[0];
        const result = await window.GeminiDiseaseAI.identifyDisease(sample.imageUrl, {
          sampleId: selectedSampleId,
          autoSpeak: true
        });

        const resultView = document.getElementById('gemini-result-view');
        resultView.style.display = 'block';
        resultView.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <span style="font-size:11px;font-weight:700;color:#065F46;background:#D4F4E4;padding:4px 10px;border-radius:9999px;">
              ✓ Saved to AgriNDB #${result.id}
            </span>
            <span style="font-size:12px;font-weight:800;color:#064E3B;">Confidence: ${result.confidence}%</span>
          </div>

          <div style="font-size:16px;font-weight:800;color:#064E3B;margin-bottom:4px;">${result.disease}</div>
          <div style="font-size:12px;color:#475569;margin-bottom:12px;">Crop: ${result.plant} • Pathogen: ${result.pathogen_type} • Severity: <strong>${result.severity}</strong></div>

          <div style="background:#fff;border-radius:12px;padding:10px 14px;box-shadow:3px 3px 8px rgba(166,180,200,0.3);margin-bottom:10px;">
            <div style="font-size:11px;font-weight:700;color:#991B1B;text-transform:uppercase;">Immediate Field Action:</div>
            <div style="font-size:12px;color:#1E293B;margin-top:2px;">${result.immediate_action}</div>
          </div>

          <div style="background:#fff;border-radius:12px;padding:10px 14px;box-shadow:3px 3px 8px rgba(166,180,200,0.3);margin-bottom:10px;">
            <div style="font-size:11px;font-weight:700;color:#065F46;text-transform:uppercase;">Recommended Prescription (Chemical &amp; Bio):</div>
            <div style="font-size:12px;color:#1E293B;margin-top:2px;"><strong>Chemical:</strong> ${result.chemical_rx}</div>
            <div style="font-size:12px;color:#1E293B;margin-top:2px;"><strong>Organic:</strong> ${result.organic_rx}</div>
          </div>

          <div style="display:flex;gap:10px;margin-top:12px;">
            <button onclick="window.speakAgriVoice('${result.voice_advisory.replace(/'/g, "\\'")}')" style="flex:1;padding:10px;border-radius:9999px;border:none;background:#EEF2F6;box-shadow:4px 4px 10px rgba(166,180,200,0.4),-4px -4px 10px #fff;font-weight:700;font-size:12px;cursor:pointer;color:#064E3B;">
              🔊 Play Voice Advisory
            </button>
            <a href="/stitch/disease_triage_queue/code.html" style="flex:1;padding:10px;border-radius:9999px;border:none;background:#98DECB;box-shadow:4px 4px 10px rgba(140,215,195,0.5),-4px -4px 10px #fff;font-weight:700;font-size:12px;text-align:center;text-decoration:none;color:#064E3B;">
              Open in Triage Queue →
            </a>
          </div>
        `;
      } catch (e) {
        showToast('Inference error: ' + e.message, 'error');
      } finally {
        runBtn.innerText = '⚡ Run Gemini Vision AI Diagnosis';
        runBtn.style.opacity = '1';
      }
    };
  }

  // ── Database Inspector Modal ──────────────────────────────
  async function openDatabaseInspectorModal() {
    let modal = document.getElementById('agrin-db-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'agrin-db-modal';
      modal.style.cssText = 'position:fixed;inset:0;z-index:99996;background:rgba(15,23,42,0.6);' +
        'backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;padding:16px;';
      document.body.appendChild(modal);
    }

    const scans = window.AgriNDB ? await window.AgriNDB.getScans() : [];
    const plots = window.AgriNDB ? await window.AgriNDB.getPlots() : [];

    modal.innerHTML = `
      <div style="background:#EEF2F6;border-radius:24px;width:100%;max-width:680px;max-height:85vh;overflow-y:auto;padding:24px;
        box-shadow:16px 16px 36px rgba(166,180,200,0.6), -16px -16px 36px rgba(255,255,255,0.95);border:1px solid rgba(255,255,255,0.8);font-family:Inter,system-ui,sans-serif;">
        
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:42px;height:42px;border-radius:14px;background:#98DECB;box-shadow:3px 3px 8px rgba(140,215,195,0.5),-3px -3px 8px #fff;display:flex;align-items:center;justify-content:center;font-size:20px;">💾</div>
            <div>
              <h2 style="font-size:17px;font-weight:800;color:#064E3B;margin:0;">AgriN Persistent Database</h2>
              <p style="font-size:11px;color:#64748B;margin:0;">IndexedDB &amp; LocalStorage Real-Time Synced Tables</p>
            </div>
          </div>
          <button id="close-db-modal" style="width:34px;height:34px;border-radius:50%;border:none;background:#EEF2F6;box-shadow:3px 3px 8px rgba(166,180,200,0.4),-3px -3px 8px #fff;font-size:15px;cursor:pointer;">✕</button>
        </div>

        <!-- Stats Chips -->
        <div style="display:flex;gap:10px;margin-bottom:16px;">
          <div style="flex:1;background:#E8ECEF;padding:12px;border-radius:14px;box-shadow:inset 3px 3px 6px rgba(166,180,200,0.3),inset -3px -3px 6px #fff;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#064E3B;">${scans.length}</div>
            <div style="font-size:11px;color:#64748B;font-weight:600;">Active Scans</div>
          </div>
          <div style="flex:1;background:#E8ECEF;padding:12px;border-radius:14px;box-shadow:inset 3px 3px 6px rgba(166,180,200,0.3),inset -3px -3px 6px #fff;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#0F766E;">${plots.length}</div>
            <div style="font-size:11px;color:#64748B;font-weight:600;">Cadastral Plots</div>
          </div>
          <div style="flex:1;background:#E8ECEF;padding:12px;border-radius:14px;box-shadow:inset 3px 3px 6px rgba(166,180,200,0.3),inset -3px -3px 6px #fff;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#10B981;">100%</div>
            <div style="font-size:11px;color:#64748B;font-weight:600;">Local-First Sync</div>
          </div>
        </div>

        <!-- Recent Records List -->
        <h4 style="font-size:13px;font-weight:700;color:#1E293B;margin:12px 0 8px 0;">Recent Plant Disease Scans</h4>
        <div style="display:flex;flex-direction:column;gap:8px;max-height:220px;overflow-y:auto;margin-bottom:16px;">
          ${scans.map(s => `
            <div style="background:#fff;border-radius:12px;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;box-shadow:2px 2px 6px rgba(166,180,200,0.3);">
              <div>
                <div style="font-size:12px;font-weight:700;color:#064E3B;">${s.disease}</div>
                <div style="font-size:11px;color:#64748B;">Plot ${s.plotId || 'N/A'} • ${new Date(s.timestamp).toLocaleTimeString()}</div>
              </div>
              <span style="font-size:11px;font-weight:700;color:${s.status === 'confirmed' ? '#065F46' : '#92400E'};background:${s.status === 'confirmed' ? '#D4F4E4' : '#FEF3C7'};padding:3px 8px;border-radius:9999px;">
                ${s.status}
              </span>
            </div>
          `).join('')}
        </div>

        <!-- Action Buttons -->
        <div style="display:flex;gap:10px;">
          <button id="export-db-json" style="flex:1;padding:12px;border-radius:9999px;border:none;background:#98DECB;box-shadow:4px 4px 10px rgba(140,215,195,0.5),-4px -4px 10px #fff;font-weight:700;font-size:13px;cursor:pointer;color:#064E3B;">
            📥 Export JSON Database
          </button>
        </div>
      </div>
    `;

    modal.style.display = 'flex';
    document.getElementById('close-db-modal').onclick = () => { modal.style.display = 'none'; };

    document.getElementById('export-db-json').onclick = async () => {
      if (window.AgriNDB) {
        const json = await window.AgriNDB.exportJSON();
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `agrin_db_backup_${Date.now()}.json`;
        a.click();
        showToast('Database exported successfully!', 'success');
      }
    };
  }

  // ── Navigation Wiring ──────────────────────────────────────
  function wireNavigation() {
    document.querySelectorAll('a, button').forEach(function(el) {
      var path = el.getAttribute('data-path');
      var href = el.getAttribute('href');
      var text = (el.innerText || '').trim().toLowerCase();

      // Convert buttons to neumorphic pill buttons where appropriate
      if (el.tagName === 'BUTTON' && !el.classList.contains('apple-map-type-btn') && !el.id.includes('dock')) {
        el.style.borderRadius = '9999px';
        el.style.boxShadow = '4px 4px 10px rgba(166,180,200,0.35), -4px -4px 10px rgba(255,255,255,0.9)';
      }

      // 1. data-path based navigation
      if (path && ROUTE_MAP[path]) {
        el.setAttribute('href', ROUTE_MAP[path]);
        el.addEventListener('click', function(e) {
          e.preventDefault();
          window.location.href = ROUTE_MAP[path];
        });
        return;
      }

      // 2. Text-based fallback for href="#" links
      if (href === '#' || (!href && el.tagName === 'A')) {
        var target = null;
        if (text.includes('disease triage') || text.includes('triage queue')) {
          target = ROUTE_MAP['disease-triage-queue'];
        } else if (text.includes('farmer') && text.includes('plot')) {
          target = ROUTE_MAP['farmer-plot-registry'];
        } else if (text.includes('geospatial') || (text.includes('command') && text.includes('map'))) {
          target = ROUTE_MAP['geospatial-command'];
        } else if (text.includes('weather') || text.includes('telemetry')) {
          target = ROUTE_MAP['telemetry-weather-stations'];
        } else if (text.includes('api') && text.includes('architecture')) {
          target = ROUTE_MAP['api-integration-architecture'];
        } else if (text.includes('scan')) {
          target = ROUTE_MAP['scan-ai'];
        } else if (text.includes('what-if') || text.includes('what if')) {
          target = ROUTE_MAP['what-if'];
        } else if (text.includes('sync') || text.includes('offline')) {
          target = ROUTE_MAP['sync'];
        }

        if (target) {
          if (el.tagName === 'A') el.setAttribute('href', target);
          el.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = target;
          });
          return;
        }
      }

      // 3. Action button handlers
      if (href === '#' || !href) {
        if (text.includes('broadcast push') || text.includes('broadcast advisory')) {
          el.addEventListener('click', function(e) {
            e.preventDefault();
            showToast('Advisory broadcasted to Ramesh Patel via WhatsApp & SMS!', 'success');
          });
        } else if (text.includes('trigger drone') || text.includes('drone scan')) {
          el.addEventListener('click', function(e) {
            e.preventDefault();
            showToast('Multispectral drone flight dispatched to Sector 4B (Alt: 45m)', 'info');
          });
        } else if (text.includes('confirm diagnosis') || text.includes('approve prescription')) {
          el.addEventListener('click', async function(e) {
            e.preventDefault();
            el.innerText = '✅ Confirmed by Officer';
            el.style.backgroundColor = '#98DECB';
            el.style.color = '#064E3B';
            el.style.pointerEvents = 'none';
            if (window.AgriNDB) {
              await window.AgriNDB.updateScan('scn-101', { status: 'confirmed' });
            }
            showToast('Diagnosis confirmed! Synced to farmer & AgriNDB database.', 'success');
          });
        } else if (text.includes('override') || text.includes('reclassify')) {
          el.addEventListener('click', async function(e) {
            e.preventDefault();
            el.innerText = '⚠️ Overridden';
            el.style.backgroundColor = '#FEF3C7';
            el.style.color = '#92400E';
            el.style.pointerEvents = 'none';
            if (window.AgriNDB) {
              await window.AgriNDB.updateScan('scn-101', { status: 'overridden' });
            }
            showToast('Classification overridden by Extension Officer.', 'warn');
          });
        } else if (text.includes('listen audio') || text.includes('voice memo') || (el.title && el.title.includes('Voice'))) {
          el.addEventListener('click', function(e) {
            e.preventDefault();
            window.speakAgriVoice("Namaste Ramesh Patel. Crop health NDVI is 0.74. Apply preventive copper fungicide spray on Sector C due to high canopy humidity.");
          });
        }
      }
    });
  }

  // ── Init ───────────────────────────────────────────────────
  function initRuntime() {
    wireNavigation();
    createNeumorphicDock();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRuntime);
  } else {
    initRuntime();
  }
})();
