/**
 * AgriN — Unified Persistent Database Engine
 * IndexedDB backed storage with localStorage mirror and multi-tab reactive sync.
 * Tables: scans, plots, triage, telemetry, settings
 */
(function() {
  'use strict';

  const DB_NAME = 'AgriN_Agronomy_DB';
  const DB_VERSION = 1;
  const BROADCAST_CHANNEL = 'agrin_db_channel';

  let dbInstance = null;
  let broadcastChannel = null;

  try {
    broadcastChannel = new BroadcastChannel(BROADCAST_CHANNEL);
    broadcastChannel.onmessage = function(event) {
      window.dispatchEvent(new CustomEvent('agrin:db-updated', { detail: event.data }));
    };
  } catch (e) {
    console.warn('BroadcastChannel not supported:', e);
  }

  function notifySync(table, action, record) {
    const detail = { table, action, record, timestamp: Date.now() };
    window.dispatchEvent(new CustomEvent('agrin:db-updated', { detail }));
    if (broadcastChannel) {
      try { broadcastChannel.postMessage(detail); } catch (err) {}
    }
  }

  // ── Database Initialization ──────────────────────────────────────────────
  function openDB() {
    return new Promise(function(resolve, reject) {
      if (dbInstance) return resolve(dbInstance);

      if (!window.indexedDB) {
        console.warn('IndexedDB unavailable, falling back to localStorage');
        return resolve(null);
      }

      const request = window.indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = function(e) {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('scans')) {
          const scanStore = db.createObjectStore('scans', { keyPath: 'id' });
          scanStore.createIndex('timestamp', 'timestamp', { unique: false });
          scanStore.createIndex('disease', 'disease', { unique: false });
        }
        if (!db.objectStoreNames.contains('plots')) {
          const plotStore = db.createObjectStore('plots', { keyPath: 'id' });
          plotStore.createIndex('cadastralId', 'cadastralId', { unique: true });
        }
        if (!db.objectStoreNames.contains('triage')) {
          const triageStore = db.createObjectStore('triage', { keyPath: 'id' });
          triageStore.createIndex('status', 'status', { unique: false });
        }
        if (!db.objectStoreNames.contains('telemetry')) {
          db.createObjectStore('telemetry', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };

      request.onsuccess = function(e) {
        dbInstance = e.target.result;
        seedInitialDataIfEmpty().then(function() {
          resolve(dbInstance);
        });
      };

      request.onerror = function(e) {
        console.error('IndexedDB open error:', e);
        resolve(null);
      };
    });
  }

  // ── Default Seed Data ───────────────────────────────────────────────────
  const SEED_PLOTS = [
    {
      id: 'plt-01',
      cadastralId: 'KNL-01',
      farmerName: 'Ramesh Patel',
      phone: '+91 98234-11029',
      village: 'Taraori, Karnal',
      crop: 'Basmati Paddy (PB-1121)',
      acreage: 4.8,
      ndvi: 0.82,
      moisture: 62,
      status: 'Healthy',
      coordinates: [29.801, 76.924],
      alerts: []
    },
    {
      id: 'plt-02',
      cadastralId: 'KNL-02',
      farmerName: 'Sukhwinder Singh',
      phone: '+91 94160-88312',
      village: 'Nissing, Karnal',
      crop: 'Wheat (HD-2967)',
      acreage: 6.2,
      ndvi: 0.79,
      moisture: 58,
      status: 'Healthy',
      coordinates: [29.742, 76.812],
      alerts: []
    },
    {
      id: 'plt-03',
      cadastralId: 'KNL-03',
      farmerName: 'Harpal Sandhu',
      phone: '+91 98122-44019',
      village: 'Gharaunda, Karnal',
      crop: 'Hybrid Tomato (Himsona)',
      acreage: 3.5,
      ndvi: 0.61,
      moisture: 49,
      status: 'Warning',
      coordinates: [29.539, 76.971],
      alerts: ['Early Blight Detected (Lesion cluster Sector 4B)']
    },
    {
      id: 'plt-04',
      cadastralId: 'KNL-04',
      farmerName: 'Baldev Choudhary',
      phone: '+91 97281-55092',
      village: 'Pehowa, Kurukshetra',
      crop: 'Barley / Mustard Intercrop',
      acreage: 5.1,
      ndvi: 0.44,
      moisture: 38,
      status: 'Critical Alert',
      coordinates: [29.982, 76.582],
      alerts: ['Stripe Rust High Infestation Risk']
    },
    {
      id: 'plt-05',
      cadastralId: 'KNL-05',
      farmerName: 'Anita Devi',
      phone: '+91 93541-99210',
      village: 'Indri, Karnal',
      crop: 'Sugarcane (Co-0238)',
      acreage: 7.0,
      ndvi: 0.77,
      moisture: 65,
      status: 'Optimal',
      coordinates: [29.881, 77.062],
      alerts: []
    }
  ];

  const SEED_SCANS = [
    {
      id: 'scn-101',
      timestamp: Date.now() - 1000 * 60 * 35,
      plant: 'Tomato (Solanum lycopersicum)',
      disease: 'Early Blight (Alternaria solani)',
      pathogen_type: 'Fungal',
      confidence: 96.4,
      severity: 'Moderate',
      symptoms: [
        'Concentric bullseye rings on mature foliage',
        'Chlorotic yellow margins surrounding brown necrotic centers',
        'Lower canopy defoliation onset'
      ],
      immediate_action: 'Prune affected lower leaves and avoid overhead sprinkler irrigation.',
      chemical_rx: 'Azoxystrobin 18.2% + Difenoconazole 11.4% SC @ 1.0 ml/L or Chlorothalonil 75 WP @ 2g/L water.',
      organic_rx: 'Bacillus subtilis bio-fungicide spray @ 5g/L combined with cold-pressed Neem oil (10,000 ppm) @ 3ml/L.',
      voice_advisory: 'Early blight fungal lesions identified on tomato foliage with 96% confidence. Apply preventive systemic fungicide spray before evening.',
      imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAK87pGlhYTQVnMMbHt5aKN0Gz4_hAZ4-5O_XP-aCtmnoMcYooTG0vzpdmJpdS0Vo9zDOzeaL485xsNSEmBLm-vwgoobxm0Bs3d60Ovt2o43cZjrRE8PAfQeBzbigsgu94CqOPE4eaAqdWTOUHLhCX9k8CfKJeJwE6qPG3HCL-Som8qpAqIKBHZa5FKyn_w1Cq1pvMJAXgF5IQ1e5qsUAZO3fPBXATzHiPVYholZ3GrwGXrnoydQaTWaw',
      farmer: 'Ramesh Patel',
      plotId: 'KNL-03',
      status: 'pending_review'
    },
    {
      id: 'scn-102',
      timestamp: Date.now() - 1000 * 60 * 120,
      plant: 'Wheat (Triticum aestivum)',
      disease: 'Stripe Rust / Yellow Rust (Puccinia striiformis)',
      pathogen_type: 'Fungal',
      confidence: 98.1,
      severity: 'Severe',
      symptoms: [
        'Linear yellow-orange stripes of urediniospore pustules',
        'Stunted flag leaf photosynthesis',
        'Rapid spore dispersion across windward canopy'
      ],
      immediate_action: 'Establish field perimeter quarantine; spray immediately to halt airborne spore burst.',
      chemical_rx: 'Propiconazole 25% EC @ 1 ml/L or Tebuconazole 25.9% EC @ 1.2 ml/L.',
      organic_rx: 'Pseudomonas fluorescens 1.0% WP liquid bio-control @ 5ml/L.',
      voice_advisory: 'Critical warning. Stripe rust detected on wheat. Airborne spread risk high. Drone fungicide application recommended.',
      imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC5tdRHWeIB8Z3A6Y6KI-B-M4FHo27ZKsS4q3U1IV_Opu5FRUopdq93uuNZDuVM8JPqb-5umTH8SGC9Xl5vOzu_Rl8Xys6urkJjH5aSH8AUYKosPh2fdnp1y0gbxGaOUFoaDToUhM_3f9bkpWtydAEAC5W-bcqTUd6HrmPZWGRA_o7cB5W9pq4FK6p1DihXWKoDe3MHi-NRpF9p6Yh5DTDUpI5taG-LpSDbTrbGftXLNSWNCQEUcR6b3g',
      farmer: 'Baldev Choudhary',
      plotId: 'KNL-04',
      status: 'confirmed'
    }
  ];

  function seedInitialDataIfEmpty() {
    return new Promise(function(resolve) {
      if (!dbInstance) {
        // Fallback to localStorage
        if (!localStorage.getItem('agrin_plots')) {
          localStorage.setItem('agrin_plots', JSON.stringify(SEED_PLOTS));
        }
        if (!localStorage.getItem('agrin_scans')) {
          localStorage.setItem('agrin_scans', JSON.stringify(SEED_SCANS));
        }
        return resolve();
      }

      const tx = dbInstance.transaction(['plots', 'scans'], 'readwrite');
      const plotStore = tx.objectStore('plots');
      const scanStore = tx.objectStore('scans');

      const countReq = plotStore.count();
      countReq.onsuccess = function() {
        if (countReq.result === 0) {
          SEED_PLOTS.forEach(p => plotStore.put(p));
          SEED_SCANS.forEach(s => scanStore.put(s));
        }
      };

      tx.oncomplete = function() {
        resolve();
      };
      tx.onerror = function() {
        resolve();
      };
    });
  }

  // ── Database Operations ──────────────────────────────────────────────────
  const AgriNDB = {
    async init() {
      return await openDB();
    },

    async getScans() {
      await openDB();
      if (!dbInstance) {
        return JSON.parse(localStorage.getItem('agrin_scans') || '[]');
      }
      return new Promise((resolve) => {
        const tx = dbInstance.transaction('scans', 'readonly');
        const store = tx.objectStore('scans');
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    },

    async saveScan(scanData) {
      await openDB();
      const record = {
        id: scanData.id || 'scn-' + Date.now(),
        timestamp: scanData.timestamp || Date.now(),
        ...scanData
      };

      if (!dbInstance) {
        const scans = JSON.parse(localStorage.getItem('agrin_scans') || '[]');
        scans.unshift(record);
        localStorage.setItem('agrin_scans', JSON.stringify(scans));
        notifySync('scans', 'insert', record);
        return record;
      }

      return new Promise((resolve, reject) => {
        const tx = dbInstance.transaction('scans', 'readwrite');
        const store = tx.objectStore('scans');
        const req = store.put(record);
        req.onsuccess = () => {
          notifySync('scans', 'insert', record);
          resolve(record);
        };
        req.onerror = (e) => reject(e);
      });
    },

    async updateScan(id, updates) {
      await openDB();
      const scans = await this.getScans();
      const scan = scans.find(s => s.id === id);
      if (!scan) return null;
      const updated = { ...scan, ...updates };

      if (!dbInstance) {
        const idx = scans.findIndex(s => s.id === id);
        scans[idx] = updated;
        localStorage.setItem('agrin_scans', JSON.stringify(scans));
        notifySync('scans', 'update', updated);
        return updated;
      }

      return new Promise((resolve) => {
        const tx = dbInstance.transaction('scans', 'readwrite');
        const store = tx.objectStore('scans');
        const req = store.put(updated);
        req.onsuccess = () => {
          notifySync('scans', 'update', updated);
          resolve(updated);
        };
      });
    },

    async getPlots() {
      await openDB();
      if (!dbInstance) {
        return JSON.parse(localStorage.getItem('agrin_plots') || '[]');
      }
      return new Promise((resolve) => {
        const tx = dbInstance.transaction('plots', 'readonly');
        const store = tx.objectStore('plots');
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    },

    async updatePlotHealth(cadastralId, ndvi, status, alert) {
      await openDB();
      const plots = await this.getPlots();
      const plot = plots.find(p => p.cadastralId === cadastralId);
      if (!plot) return null;

      plot.ndvi = ndvi;
      if (status) plot.status = status;
      if (alert && !plot.alerts.includes(alert)) {
        plot.alerts.push(alert);
      }

      if (!dbInstance) {
        const idx = plots.findIndex(p => p.cadastralId === cadastralId);
        plots[idx] = plot;
        localStorage.setItem('agrin_plots', JSON.stringify(plots));
        notifySync('plots', 'update', plot);
        return plot;
      }

      return new Promise((resolve) => {
        const tx = dbInstance.transaction('plots', 'readwrite');
        const store = tx.objectStore('plots');
        const req = store.put(plot);
        req.onsuccess = () => {
          notifySync('plots', 'update', plot);
          resolve(plot);
        };
      });
    },

    async getSettings() {
      const local = localStorage.getItem('agrin_settings');
      return local ? JSON.parse(local) : {
        geminiApiKey: localStorage.getItem('gemini_api_key') || '',
        appleMapKitToken: localStorage.getItem('apple_mapkit_token') || '',
        syncInterval: 30
      };
    },

    async saveSettings(settings) {
      localStorage.setItem('agrin_settings', JSON.stringify(settings));
      if (settings.geminiApiKey) {
        localStorage.setItem('gemini_api_key', settings.geminiApiKey);
      }
      if (settings.appleMapKitToken) {
        localStorage.setItem('apple_mapkit_token', settings.appleMapKitToken);
      }
      notifySync('settings', 'update', settings);
      return settings;
    },

    async exportJSON() {
      const scans = await this.getScans();
      const plots = await this.getPlots();
      const settings = await this.getSettings();
      return JSON.stringify({
        database: DB_NAME,
        version: DB_VERSION,
        exportedAt: new Date().toISOString(),
        tables: { scans, plots, settings }
      }, null, 2);
    }
  };

  // Expose globally
  window.AgriNDB = AgriNDB;
  AgriNDB.init();
})();
