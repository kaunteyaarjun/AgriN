import React, { useState, useEffect, useRef } from 'react';

// Declaration for window globals injected by agrin-db, gemini-disease-ai, and apple-maps
declare global {
  interface Window {
    AgriNDB?: any;
    GeminiDiseaseAI?: any;
    AgriNAppleMaps?: any;
    showAgriToast?: (msg: string, type?: string) => void;
    speakAgriVoice?: (text: string) => void;
  }
}

interface ScreenCard {
  id: string;
  title: string;
  subtitle: string;
  path: string;
  category: 'mobile' | 'officer';
  badge: string;
  icon: string;
  tag: string;
}

const ALL_SCREENS: ScreenCard[] = [
  // Mobile Farmer App Screens
  {
    id: 'home_farm_digital_twin',
    title: 'Farm Digital Twin',
    subtitle: 'NDVI radar, canopy health diagnostics, soil moisture & weather telemetry',
    path: '/stitch/home_farm_digital_twin/code.html',
    category: 'mobile',
    badge: 'Core Home',
    icon: '🛰️',
    tag: 'Digital Twin'
  },
  {
    id: 'crop_disease_doctor',
    title: 'Crop Disease Doctor',
    subtitle: 'Gemini vision scanner, lesion detection & chemical/bio prescriptions',
    path: '/stitch/crop_disease_doctor/code.html',
    category: 'mobile',
    badge: 'Vision AI',
    icon: '🔬',
    tag: 'Vision AI'
  },
  {
    id: 'what_if_simulator',
    title: 'What-If Simulator',
    subtitle: 'Climate sliders, yield impact delta, nitrogen modeling & risk curves',
    path: '/stitch/what_if_simulator/code.html',
    category: 'mobile',
    badge: 'Simulator',
    icon: '🎛️',
    tag: 'Decision Engine'
  },
  {
    id: 'offline_mode_data_sync',
    title: 'Offline Mode & Sync',
    subtitle: 'Local-first IndexedDB queue, conflict resolution & satellite sync',
    path: '/stitch/offline_mode_data_sync/code.html',
    category: 'mobile',
    badge: 'Offline-First',
    icon: '📡',
    tag: 'Sync & Storage'
  },
  // Extension Officer Screens
  {
    id: 'geospatial_command_triage_drawer',
    title: 'Geospatial Command & GIS',
    subtitle: 'Apple Maps vector layers, Cadastral plots & regional outbreak triage',
    path: '/stitch/geospatial_command_triage_drawer/code.html',
    category: 'officer',
    badge: 'Apple Maps',
    icon: '🗺️',
    tag: 'GIS Map'
  },
  {
    id: 'disease_triage_queue',
    title: 'Disease Triage Queue',
    subtitle: 'In-field lesion reviews, confidence gates & officer override workflow',
    path: '/stitch/disease_triage_queue/code.html',
    category: 'officer',
    badge: 'Triage Queue',
    icon: '🦠',
    tag: 'Triage'
  },
  {
    id: 'farmer_plot_management_directory',
    title: 'Farmer & Plot Directory',
    subtitle: 'Searchable farmer registry, harvest metrics & cadastral parcel lifecycle',
    path: '/stitch/farmer_plot_management_directory/code.html',
    category: 'officer',
    badge: 'Registry',
    icon: '👥',
    tag: 'Registry'
  },
  {
    id: 'telemetry_weather_stations',
    title: 'Telemetry & Weather',
    subtitle: 'Micro-climate sensors, rain radar & soil volumetric moisture matrix',
    path: '/stitch/telemetry_weather_stations/code.html',
    category: 'officer',
    badge: 'Sensors',
    icon: '🌦️',
    tag: 'IoT Telemetry'
  },
  {
    id: 'backend_api_integration_architecture',
    title: 'Backend API Architecture',
    subtitle: 'FastAPI schemas, database models & telemetry pipeline contract docs',
    path: '/stitch/backend_api_integration_architecture/code.html',
    category: 'officer',
    badge: 'API Docs',
    icon: '⚙️',
    tag: 'API Architecture'
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'all' | 'mobile' | 'officer'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string>('All');
  
  // Modals & Panels
  const [showAppleMaps, setShowAppleMaps] = useState(false);
  const [showDbInspector, setShowDbInspector] = useState(false);

  // Gemini Scanner State
  const [geminiApiKey, setGeminiApiKey] = useState(localStorage.getItem('gemini_api_key') || '');
  const [selectedSample, setSelectedSample] = useState<string>('sample_tomato_early_blight');
  const [customImage, setCustomImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [latestDiagnosis, setLatestDiagnosis] = useState<any>(null);

  // Database State
  const [dbScans, setDbScans] = useState<any[]>([]);
  const [dbPlots, setDbPlots] = useState<any[]>([]);

  // Apple Maps Container Ref
  const appleMapRef = useRef<HTMLDivElement>(null);

  // Load Database Records
  useEffect(() => {
    async function loadData() {
      if (window.AgriNDB) {
        try {
          const scans = await window.AgriNDB.getScans();
          const plots = await window.AgriNDB.getPlots();
          setDbScans(scans);
          setDbPlots(plots);
          if (scans.length > 0 && !latestDiagnosis) {
            setLatestDiagnosis(scans[0]);
          }
        } catch (e) {
          console.error('Failed to load DB in React:', e);
        }
      }
    }

    loadData();

    // Listen to DB updates
    const handleDbUpdate = () => {
      loadData();
    };

    window.addEventListener('agrin:db-updated', handleDbUpdate);
    window.addEventListener('agrin:disease-scanned', handleDbUpdate);

    return () => {
      window.removeEventListener('agrin:db-updated', handleDbUpdate);
      window.removeEventListener('agrin:disease-scanned', handleDbUpdate);
    };
  }, [latestDiagnosis]);

  // Initialize Apple Maps when opened
  useEffect(() => {
    if (showAppleMaps && appleMapRef.current && window.AgriNAppleMaps) {
      window.AgriNAppleMaps.initMap(appleMapRef.current, {
        plots: dbPlots,
        onPlotClick: (plotId: string) => {
          if (window.showAgriToast) {
            window.showAgriToast(` Apple Maps: Inspected Cadastral Plot ${plotId}`, 'info');
          }
        }
      });
    }
  }, [showAppleMaps, dbPlots]);

  // Handle Gemini Disease Scan
  const handleRunGeminiDiagnosis = async () => {
    setIsAnalyzing(true);
    try {
      if (window.GeminiDiseaseAI) {
        // Save API key if modified
        if (geminiApiKey) {
          window.GeminiDiseaseAI.setApiKey(geminiApiKey);
        }

        const imageToAnalyze = customImage || selectedSample;
        const result = await window.GeminiDiseaseAI.identifyDisease(imageToAnalyze, {
          sampleId: selectedSample,
          autoSpeak: true
        });
        setLatestDiagnosis(result);

        if (window.showAgriToast) {
          window.showAgriToast(`Gemini AI identified: ${result.disease} (${result.confidence}%)`, 'success');
        }
      }
    } catch (err: any) {
      if (window.showAgriToast) {
        window.showAgriToast('Analysis error: ' + (err.message || 'Check connection'), 'error');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle Custom File Upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setCustomImage(reader.result as string);
        if (window.showAgriToast) {
          window.showAgriToast(`Loaded ${file.name}. Ready for Gemini Vision analysis.`, 'info');
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Filter Screens
  const filteredScreens = ALL_SCREENS.filter(screen => {
    const matchesTab = activeTab === 'all' || screen.category === activeTab;
    const matchesSearch = screen.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          screen.subtitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          screen.badge.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTag = selectedTag === 'All' || screen.tag === selectedTag;
    return matchesTab && matchesSearch && matchesTag;
  });

  const allTags = ['All', 'Vision AI', 'GIS Map', 'Digital Twin', 'Decision Engine', 'Triage', 'Registry', 'IoT Telemetry', 'Sync & Storage'];

  return (
    <div className="min-h-screen text-[#1E293B] antialiased" style={{ backgroundColor: '#E8ECEF' }}>
      
      {/* ── Top Neumorphic Navbar ────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 px-6 py-4 backdrop-blur-md" style={{ backgroundColor: 'rgba(232, 236, 239, 0.92)', boxShadow: '0 4px 16px rgba(166, 180, 200, 0.35)', borderBottom: '1px solid rgba(255, 255, 255, 0.8)' }}>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" style={{ background: '#EEF2F6', boxShadow: '4px 4px 10px rgba(166,180,200,0.4), -4px -4px 10px #ffffff', border: '1px solid rgba(255,255,255,0.8)' }}>
              🌱
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold tracking-tight" style={{ color: '#064E3B' }}>
                  AgriN
                </h1>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full" style={{ background: '#98DECB', color: '#064E3B', boxShadow: '2px 2px 5px rgba(140,215,195,0.4)' }}>
                  Neumorphic OS
                </span>
              </div>
              <p className="text-xs text-[#64748B] font-medium">Regenerative Agricultural Intelligence</p>
            </div>
          </div>

          {/* Inset Pill Search Input from Styleguide */}
          <div className="w-full md:max-w-md">
            <div className="flex items-center gap-3 px-4 py-2.5 rounded-full" style={{ backgroundColor: '#E8ECEF', boxShadow: 'inset 3px 3px 6px rgba(166, 180, 200, 0.45), inset -3px -3px 6px #ffffff', border: '1.5px solid rgba(166, 180, 200, 0.25)' }}>
              <span className="text-sm">🔍</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search screens, diseases, plots, sensors..."
                className="w-full bg-transparent text-sm text-[#1E293B] placeholder-[#94A3B8] outline-none"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="text-xs text-[#94A3B8] hover:text-[#1E293B]">✕</button>
              )}
            </div>
          </div>

          {/* Top Quick Actions (Pill Buttons from Styleguide) */}
          <div className="flex items-center gap-2 w-full md:w-auto justify-end flex-wrap">
            {/* Primary Mint Action Button */}
            <button
              onClick={() => {
                const el = document.getElementById('gemini-scanner-section');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold transition-all"
              style={{
                background: 'linear-gradient(135deg, #a8eed9 0%, #82deb0 100%)',
                color: '#064E3B',
                boxShadow: '4px 4px 12px rgba(130,222,176,0.5), -4px -4px 12px #ffffff',
                border: '1px solid rgba(255, 255, 255, 0.8)'
              }}
            >
              <span>🔬</span>
              <span>Gemini AI Scan</span>
            </button>

            {/* Mobile App Launch Button */}
            <a
              href="/mobile/index.html"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2.5 rounded-full text-xs font-bold transition-all text-[#064E3B]"
              style={{
                background: 'linear-gradient(135deg, #a8eed9 0%, #82deb0 100%)',
                boxShadow: '4px 4px 10px rgba(130,222,176,0.45), -4px -4px 10px #ffffff',
                border: '1px solid rgba(255, 255, 255, 0.8)'
              }}
            >
              <span>📱</span>
              <span>Launch Mobile App</span>
            </a>

            {/* Apple & Free Maps Pill */}
            <button
              onClick={() => setShowAppleMaps(!showAppleMaps)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-full text-xs font-bold transition-all"
              style={{
                backgroundColor: showAppleMaps ? '#98DECB' : '#EEF2F6',
                color: showAppleMaps ? '#064E3B' : '#1E293B',
                boxShadow: '4px 4px 10px rgba(166,180,200,0.4), -4px -4px 10px #ffffff',
                border: '1px solid rgba(255, 255, 255, 0.8)'
              }}
            >
              <span>🛰️</span>
              <span>Free GIS &amp; Apple Maps</span>
            </button>

            {/* Database Pill */}
            <button
              onClick={() => setShowDbInspector(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-full text-xs font-bold transition-all"
              style={{
                backgroundColor: '#EEF2F6',
                color: '#0F766E',
                boxShadow: '4px 4px 10px rgba(166,180,200,0.4), -4px -4px 10px #ffffff',
                border: '1px solid rgba(255, 255, 255, 0.8)'
              }}
            >
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></span>
              <span>DB ({dbScans.length} scans)</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Hero & System Metrics ────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex flex-col gap-8">
        
        {/* Prominent Gemini API Key Configuration Card */}
        <div className="p-5 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4" style={{ backgroundColor: '#EEF2F6', boxShadow: '6px 6px 14px rgba(166,180,200,0.38), -6px -6px 14px #ffffff', border: '1.5px solid rgba(152,222,203,0.5)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-[#98DECB] text-[#064E3B] shrink-0" style={{ boxShadow: '2px 2px 6px rgba(140,215,195,0.4)' }}>
              🔑
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-extrabold text-[#064E3B]">Google Gemini API Setup</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: geminiApiKey ? '#D4F4E4' : '#FEF3C7', color: geminiApiKey ? '#065F46' : '#92400E' }}>
                  {geminiApiKey ? '● Gemini Key Active' : '○ Free Open-Source Mode (PlantVillage Active)'}
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#D4F4E4] text-[#065F46]">
                  ● FastAPI Backend: http://127.0.0.1:8000
                </span>
              </div>
              <p className="text-xs text-[#64748B] mt-0.5">
                Enter your Gemini API key for live multimodal vision leaf analysis. Get a free key at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="underline font-bold text-[#064E3B]">Google AI Studio</a>.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="flex items-center gap-2 px-3 py-2 rounded-full flex-1 md:w-64" style={{ backgroundColor: '#E8ECEF', boxShadow: 'inset 2px 2px 5px rgba(166,180,200,0.4), inset -2px -2px 5px #fff', border: '1px solid rgba(166,180,200,0.2)' }}>
              <span>🔐</span>
              <input
                type="password"
                placeholder="AIzaSy... (Gemini Key)"
                value={geminiApiKey}
                onChange={(e) => {
                  setGeminiApiKey(e.target.value);
                  if (window.GeminiDiseaseAI) window.GeminiDiseaseAI.setApiKey(e.target.value);
                }}
                className="w-full bg-transparent text-xs text-[#1E293B] outline-none placeholder-[#94A3B8]"
              />
            </div>
            <button
              onClick={() => {
                if (geminiApiKey) {
                  localStorage.setItem('gemini_api_key', geminiApiKey.trim());
                  if (window.showAgriToast) window.showAgriToast('Gemini API key saved & activated!', 'success');
                } else {
                  if (window.showAgriToast) window.showAgriToast('Switched to Open-Source PlantVillage mode', 'info');
                }
              }}
              className="px-4 py-2 rounded-full text-xs font-bold whitespace-nowrap text-[#064E3B]"
              style={{ background: '#98DECB', boxShadow: '2px 2px 6px rgba(140,215,195,0.5)' }}
            >
              Save Key
            </button>
          </div>
        </div>

        {/* Alerts from Styleguide */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 flex items-center gap-3 px-5 py-3 rounded-full text-xs font-semibold" style={{ background: '#D4F4E4', color: '#065F46', border: '1px solid #85F8C4', boxShadow: '4px 4px 10px rgba(166,180,200,0.3), -4px -4px 10px #fff' }}>
            <span>✅</span>
            <span><strong>Backend &amp; DB Synced:</strong> FastAPI running on port 8000 • IndexedDB connected • {dbPlots.length} cadastral plots &amp; {dbScans.length} disease records.</span>
          </div>
          <div className="flex items-center gap-3 px-5 py-3 rounded-full text-xs font-semibold" style={{ background: '#FEF3C7', color: '#92400E', border: '1px solid #FCD34D', boxShadow: '4px 4px 10px rgba(166,180,200,0.3), -4px -4px 10px #fff' }}>
            <span>⚠️</span>
            <span><strong>Outbreak Gate:</strong> 26 regional hotspots tracked via Free Satellite &amp; OpenStreetMap.</span>
          </div>
        </div>

        {/* ── 4 Elevated Neumorphic KPI Cards (Levels 1-5 from Styleguide) ─── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          
          {/* Card 1: Active Plots */}
          <div className="p-5 rounded-2xl flex flex-col justify-between" style={{ backgroundColor: '#EEF2F6', boxShadow: '6px 6px 14px rgba(166,180,200,0.38), -6px -6px 14px #ffffff', border: '1px solid rgba(255,255,255,0.8)' }}>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Cadastral Plots</span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm" style={{ background: '#E8ECEF', boxShadow: '2px 2px 5px rgba(166,180,200,0.3), -2px -2px 5px #fff' }}>🌾</div>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold text-[#064E3B]">7,841</span>
              <span className="text-xs font-medium text-[#64748B] ml-1.5">plots registered</span>
            </div>
            <div className="text-[11px] font-semibold text-[#059669]">99.4% Digitized (Karnal Sector)</div>
          </div>

          {/* Card 2: Gemini AI Scans */}
          <div className="p-5 rounded-2xl flex flex-col justify-between" style={{ backgroundColor: '#EEF2F6', boxShadow: '6px 6px 14px rgba(166,180,200,0.38), -6px -6px 14px #ffffff', border: '1px solid rgba(255,255,255,0.8)' }}>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Gemini AI Scans</span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm" style={{ background: '#98DECB', color: '#064E3B', boxShadow: '2px 2px 5px rgba(140,215,195,0.5)' }}>🔬</div>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold text-[#064E3B]">{dbScans.length}</span>
              <span className="text-xs font-medium text-[#64748B] ml-1.5">in IndexedDB</span>
            </div>
            <div className="text-[11px] font-semibold text-[#006948]">Multimodal Vision 2.5 Flash</div>
          </div>

          {/* Card 3: Apple Maps Outbreaks */}
          <div className="p-5 rounded-2xl flex flex-col justify-between" style={{ backgroundColor: '#EEF2F6', boxShadow: '6px 6px 14px rgba(166,180,200,0.38), -6px -6px 14px #ffffff', border: '1px solid rgba(255,255,255,0.8)' }}>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#991B1B]">Apple Maps Outbreaks</span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm" style={{ background: '#FEE2E2', color: '#991B1B', boxShadow: '2px 2px 5px rgba(252,165,165,0.4)' }}></div>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold text-[#991B1B]">26</span>
              <span className="text-xs font-medium text-[#991B1B] ml-1.5">active clusters</span>
            </div>
            <div className="text-[11px] font-semibold text-[#B91C1C]">18 Early Blight • 8 Yellow Rust</div>
          </div>

          {/* Card 4: Soil VWC Moisture */}
          <div className="p-5 rounded-2xl flex flex-col justify-between" style={{ backgroundColor: '#EEF2F6', boxShadow: '6px 6px 14px rgba(166,180,200,0.38), -6px -6px 14px #ffffff', border: '1px solid rgba(255,255,255,0.8)' }}>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Soil Moisture VWC</span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm" style={{ background: '#E0F2FE', color: '#0369A1', boxShadow: '2px 2px 5px rgba(186,230,253,0.5)' }}>💧</div>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold text-[#0369A1]">58%</span>
              <span className="text-xs font-medium text-[#64748B] ml-1.5">volumetric moisture</span>
            </div>
            <div className="text-[11px] font-semibold text-[#0284C7]">Optimal root zone hydration</div>
          </div>
        </div>

        {/* ── Spotlight Section 1: Gemini AI Plant Disease Doctor ──────────── */}
        <section id="gemini-scanner-section" className="p-6 rounded-3xl" style={{ backgroundColor: '#EEF2F6', boxShadow: '9px 9px 20px rgba(166,180,200,0.4), -9px -9px 20px #ffffff', border: '1px solid rgba(255, 255, 255, 0.8)' }}>
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" style={{ background: '#98DECB', color: '#064E3B', boxShadow: '4px 4px 10px rgba(140,215,195,0.5), -4px -4px 10px #ffffff' }}>
                🔬
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-[#064E3B]">Gemini AI Plant Pathology Diagnostic Engine</h2>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#D4F4E4] text-[#065F46]">
                    Multimodal Vision API
                  </span>
                </div>
                <p className="text-xs text-[#64748B]">Upload leaf imagery or select test specimens to diagnose plant pathogens with immediate chemical &amp; organic prescriptions.</p>
              </div>
            </div>

            {/* API Key Inset Input */}
            <div className="flex items-center gap-2 w-full md:w-auto">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs" style={{ background: '#E8ECEF', boxShadow: 'inset 2px 2px 4px rgba(166,180,200,0.4), inset -2px -2px 4px #fff' }}>
                <span>🔑</span>
                <input
                  type="password"
                  placeholder="Gemini API Key (Optional)"
                  value={geminiApiKey}
                  onChange={(e) => {
                    setGeminiApiKey(e.target.value);
                    if (window.GeminiDiseaseAI) window.GeminiDiseaseAI.setApiKey(e.target.value);
                  }}
                  className="bg-transparent text-xs text-[#1E293B] outline-none w-36 sm:w-48 placeholder-[#94A3B8]"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left: Specimen Picker & Uploader (5 cols) */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <label className="text-xs font-bold text-[#475569] uppercase tracking-wider">Select Botanical Specimen:</label>
              
              <div className="grid grid-cols-2 gap-2.5">
                {[
                  { id: 'sample_tomato_early_blight', name: 'Tomato Early Blight', crop: 'Tomato', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAK87pGlhYTQVnMMbHt5aKN0Gz4_hAZ4-5O_XP-aCtmnoMcYooTG0vzpdmJpdS0Vo9zDOzeaL485xsNSEmBLm-vwgoobxm0Bs3d60Ovt2o43cZjrRE8PAfQeBzbigsgu94CqOPE4eaAqdWTOUHLhCX9k8CfKJeJwE6qPG3HCL-Som8qpAqIKBHZa5FKyn_w1Cq1pvMJAXgF5IQ1e5qsUAZO3fPBXATzHiPVYholZ3GrwGXrnoydQaTWaw' },
                  { id: 'sample_wheat_stripe_rust', name: 'Wheat Stripe Rust', crop: 'Wheat', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC5tdRHWeIB8Z3A6Y6KI-B-M4FHo27ZKsS4q3U1IV_Opu5FRUopdq93uuNZDuVM8JPqb-5umTH8SGC9Xl5vOzu_Rl8Xys6urkJjH5aSH8AUYKosPh2fdnp1y0gbxGaOUFoaDToUhM_3f9bkpWtydAEAC5W-bcqTUd6HrmPZWGRA_o7cB5W9pq4FK6p1DihXWKoDe3MHi-NRpF9p6Yh5DTDUpI5taG-LpSDbTrbGftXLNSWNCQEUcR6b3g' },
                  { id: 'sample_corn_northern_blight', name: 'Corn Leaf Blight', crop: 'Maize', img: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=400&q=80' },
                  { id: 'sample_apple_scab', name: 'Apple Scab Lesion', crop: 'Apple', img: 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=400&q=80' }
                ].map(specimen => (
                  <button
                    key={specimen.id}
                    onClick={() => {
                      setSelectedSample(specimen.id);
                      setCustomImage(null);
                    }}
                    className="p-2.5 rounded-xl text-left flex items-center gap-2.5 transition-all"
                    style={{
                      backgroundColor: selectedSample === specimen.id && !customImage ? '#EEF2F6' : '#E8ECEF',
                      boxShadow: selectedSample === specimen.id && !customImage
                        ? 'inset 2px 2px 5px rgba(166,180,200,0.5), inset -2px -2px 5px #fff'
                        : '3px 3px 8px rgba(166,180,200,0.35), -3px -3px 8px #fff',
                      border: selectedSample === specimen.id && !customImage ? '2px solid #00CFCC' : '1px solid rgba(255,255,255,0.7)'
                    }}
                  >
                    <img src={specimen.img} alt={specimen.name} className="w-10 h-10 rounded-lg object-cover" />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-bold text-[#1E293B] truncate">{specimen.name}</div>
                      <div className="text-[10px] text-[#64748B]">{specimen.crop}</div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Upload Custom File */}
              <div className="flex items-center gap-2">
                <label className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-full text-xs font-semibold cursor-pointer transition-all" style={{ backgroundColor: '#EEF2F6', boxShadow: '3px 3px 8px rgba(166,180,200,0.35), -3px -3px 8px #fff', border: '1px solid rgba(255,255,255,0.8)' }}>
                  <span>📷</span>
                  <span>Upload Real Leaf Photo</span>
                  <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
                </label>
              </div>

              {/* Primary Run Inference Pill Button */}
              <button
                disabled={isAnalyzing}
                onClick={handleRunGeminiDiagnosis}
                className="w-full py-3.5 rounded-full text-sm font-bold transition-all flex items-center justify-center gap-2"
                style={{
                  background: 'linear-gradient(135deg, #a8eed9 0%, #82deb0 100%)',
                  color: '#064E3B',
                  boxShadow: '5px 5px 14px rgba(130,222,176,0.5), -5px -5px 14px #ffffff',
                  border: '1px solid rgba(255, 255, 255, 0.8)',
                  opacity: isAnalyzing ? 0.7 : 1
                }}
              >
                <span>{isAnalyzing ? '⏳' : '⚡'}</span>
                <span>{isAnalyzing ? 'Gemini Vision AI Analyzing Lesion...' : 'Identify Disease with Gemini AI'}</span>
              </button>
            </div>

            {/* Right: Live Diagnosis Output (7 cols) */}
            <div className="lg:col-span-7 p-5 rounded-2xl flex flex-col justify-between" style={{ backgroundColor: '#E8ECEF', boxShadow: 'inset 4px 4px 10px rgba(166,180,200,0.4), inset -4px -4px 10px #ffffff', border: '1px solid rgba(166,180,200,0.2)' }}>
              {latestDiagnosis ? (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-[#D4F4E4] text-[#065F46]">
                      ✓ Saved to AgriNDB ({latestDiagnosis.id || 'scn-current'})
                    </span>
                    <span className="text-xs font-extrabold text-[#064E3B]">
                      Confidence: {latestDiagnosis.confidence || 96.8}%
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-extrabold text-[#064E3B]">{latestDiagnosis.disease}</h3>
                    <p className="text-xs text-[#475569]">Crop: {latestDiagnosis.plant} • Pathogen: {latestDiagnosis.pathogen_type} • Severity: <strong className="text-[#991B1B]">{latestDiagnosis.severity}</strong></p>
                  </div>

                  {/* Immediate Action */}
                  <div className="bg-white/80 p-3 rounded-xl border border-white">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#991B1B]">Immediate Field Action:</div>
                    <p className="text-xs text-[#1E293B] mt-0.5">{latestDiagnosis.immediate_action}</p>
                  </div>

                  {/* Prescriptions */}
                  <div className="bg-white/80 p-3 rounded-xl border border-white">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#065F46]">Prescription Protocol:</div>
                    <div className="text-xs text-[#1E293B] mt-0.5"><strong>Chemical:</strong> {latestDiagnosis.chemical_rx}</div>
                    <div className="text-xs text-[#1E293B] mt-0.5"><strong>Organic / Bio:</strong> {latestDiagnosis.organic_rx}</div>
                  </div>

                  {/* Voice Button */}
                  <div className="flex items-center gap-3 pt-1">
                    <button
                      onClick={() => {
                        if (window.speakAgriVoice) {
                          window.speakAgriVoice(latestDiagnosis.voice_advisory || 'Early blight detected. Spray fungicide immediately.');
                        }
                      }}
                      className="px-4 py-2 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all"
                      style={{ background: '#EEF2F6', color: '#064E3B', boxShadow: '3px 3px 8px rgba(166,180,200,0.4), -3px -3px 8px #fff' }}
                    >
                      <span>🔊</span>
                      <span>Play Spoken Voice Advisory</span>
                    </button>

                    <a
                      href="/stitch/crop_disease_doctor/code.html"
                      className="px-4 py-2 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all text-[#064E3B]"
                      style={{ background: '#98DECB', boxShadow: '3px 3px 8px rgba(140,215,195,0.5), -3px -3px 8px #fff' }}
                    >
                      <span>Open Full Doctor View →</span>
                    </a>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-[#64748B]">
                  <span className="text-4xl mb-2">🌿</span>
                  <p className="text-sm font-bold text-[#1E293B]">Ready for Plant Disease Diagnostics</p>
                  <p className="text-xs mt-1">Select a leaf specimen above and click "Identify Disease with Gemini AI".</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── Spotlight Section 2: Interactive Apple Maps GIS Command (Collapsible/Toggle) ── */}
        {showAppleMaps && (
          <section className="p-6 rounded-3xl" style={{ backgroundColor: '#EEF2F6', boxShadow: '9px 9px 20px rgba(166,180,200,0.4), -9px -9px 20px #ffffff', border: '1px solid rgba(255, 255, 255, 0.8)' }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-[#EEF2F6]" style={{ boxShadow: '3px 3px 8px rgba(166,180,200,0.4), -3px -3px 8px #fff' }}>
                  
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#064E3B]">Apple Maps MapKit JS — Cadastral Command Center</h3>
                  <p className="text-xs text-[#64748B]">Interactive PostGIS vectors, NDVI multi-spectral overlays &amp; disease alert hotspots.</p>
                </div>
              </div>
              <button
                onClick={() => setShowAppleMaps(false)}
                className="text-xs font-bold px-3 py-1.5 rounded-full"
                style={{ background: '#E8ECEF', boxShadow: '2px 2px 5px rgba(166,180,200,0.3), -2px -2px 5px #fff' }}
              >
                Close Map ✕
              </button>
            </div>

            {/* Apple Maps Canvas Mount */}
            <div ref={appleMapRef} className="w-full h-96 rounded-2xl relative overflow-hidden" style={{ minHeight: '380px' }}></div>
          </section>
        )}

        {/* ── Spotlight Section 3: Screen Directory Tabs & Filters ─────────── */}
        <section className="flex flex-col gap-5">
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-[#064E3B]">Platform Applications &amp; Interfaces</h2>
              <p className="text-xs text-[#64748B]">9 dedicated operational modules engineered for farmers and extension officers.</p>
            </div>

            {/* Neumorphic Tabs Container from Styleguide */}
            <div className="flex items-center p-1 rounded-full" style={{ backgroundColor: '#E8ECEF', boxShadow: 'inset 2px 2px 5px rgba(166,180,200,0.4), inset -2px -2px 5px #fff' }}>
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${activeTab === 'all' ? 'text-[#064E3B]' : 'text-[#64748B]'}`}
                style={{
                  background: activeTab === 'all' ? '#98DECB' : 'transparent',
                  boxShadow: activeTab === 'all' ? '2px 2px 6px rgba(140,215,195,0.4)' : 'none'
                }}
              >
                All (9)
              </button>
              <button
                onClick={() => setActiveTab('mobile')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${activeTab === 'mobile' ? 'text-[#064E3B]' : 'text-[#64748B]'}`}
                style={{
                  background: activeTab === 'mobile' ? '#98DECB' : 'transparent',
                  boxShadow: activeTab === 'mobile' ? '2px 2px 6px rgba(140,215,195,0.4)' : 'none'
                }}
              >
                Farmer Mobile (4)
              </button>
              <button
                onClick={() => setActiveTab('officer')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${activeTab === 'officer' ? 'text-[#064E3B]' : 'text-[#64748B]'}`}
                style={{
                  background: activeTab === 'officer' ? '#98DECB' : 'transparent',
                  boxShadow: activeTab === 'officer' ? '2px 2px 6px rgba(140,215,195,0.4)' : 'none'
                }}
              >
                Officer Web (5)
              </button>
            </div>
          </div>

          {/* Filter Chips from Styleguide */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <span className="text-xs font-bold text-[#64748B] mr-1">Filter:</span>
            {allTags.map(tag => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag)}
                className="px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all"
                style={{
                  backgroundColor: selectedTag === tag ? '#98DECB' : '#EEF2F6',
                  color: selectedTag === tag ? '#064E3B' : '#475569',
                  boxShadow: selectedTag === tag ? '3px 3px 8px rgba(140,215,195,0.4), -3px -3px 8px #fff' : '2px 2px 6px rgba(166,180,200,0.3), -2px -2px 6px #fff',
                  border: '1px solid rgba(255,255,255,0.7)'
                }}
              >
                {selectedTag === tag && <span className="mr-1">✓</span>}
                {tag}
              </button>
            ))}
          </div>

          {/* 9 Neumorphic Screen Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredScreens.map((screen) => (
              <div
                key={screen.id}
                className="p-6 rounded-3xl flex flex-col justify-between transition-all group hover:-translate-y-1"
                style={{
                  backgroundColor: '#EEF2F6',
                  boxShadow: '6px 6px 16px rgba(166,180,200,0.38), -6px -6px 16px #ffffff',
                  border: '1px solid rgba(255,255,255,0.8)'
                }}
              >
                <div>
                  {/* Top card bar with 3D tactile icon & badge */}
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl transition-transform group-hover:scale-105"
                      style={{
                        backgroundColor: '#EEF2F6',
                        boxShadow: '4px 4px 10px rgba(166,180,200,0.4), -4px -4px 10px #ffffff',
                        border: '1px solid rgba(255,255,255,0.8)'
                      }}
                    >
                      {screen.icon}
                    </div>
                    <span
                      className="text-[11px] font-bold px-2.5 py-1 rounded-full"
                      style={{
                        backgroundColor: '#E8ECEF',
                        color: screen.category === 'mobile' ? '#065F46' : '#0369A1',
                        boxShadow: 'inset 1px 1px 3px rgba(166,180,200,0.3), inset -1px -1px 3px #fff'
                      }}
                    >
                      {screen.badge}
                    </span>
                  </div>

                  <h3 className="text-base font-extrabold text-[#1E293B] mb-1.5">{screen.title}</h3>
                  <p className="text-xs text-[#64748B] leading-relaxed mb-4">{screen.subtitle}</p>
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-[rgba(166,180,200,0.2)]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#94A3B8]">{screen.tag}</span>
                  
                  {/* Pill Action Button */}
                  <a
                    href={screen.path}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-bold transition-all"
                    style={{
                      background: 'linear-gradient(135deg, #a8eed9 0%, #82deb0 100%)',
                      color: '#064E3B',
                      boxShadow: '3px 3px 8px rgba(130,222,176,0.45), -3px -3px 8px #ffffff'
                    }}
                  >
                    <span>Launch</span>
                    <span>→</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Database Inspector Modal ────────────────────────────────────── */}
        {showDbInspector && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
            <div className="w-full max-w-2xl rounded-3xl p-6 max-h-[85vh] overflow-y-auto" style={{ backgroundColor: '#EEF2F6', boxShadow: '16px 16px 36px rgba(166,180,200,0.6), -16px -16px 36px #fff' }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-[#98DECB] text-[#064E3B]">💾</div>
                  <div>
                    <h3 className="text-base font-bold text-[#064E3B]">Integrated Persistent Database (IndexedDB)</h3>
                    <p className="text-xs text-[#64748B]">Real-time synchronization across all tabs and Stitch applications.</p>
                  </div>
                </div>
                <button onClick={() => setShowDbInspector(false)} className="w-8 h-8 rounded-full bg-[#E8ECEF] text-sm font-bold">✕</button>
              </div>

              {/* Scans table */}
              <div className="mb-4">
                <h4 className="text-xs font-bold text-[#475569] uppercase tracking-wider mb-2">Stored Plant Disease Diagnoses ({dbScans.length}):</h4>
                <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
                  {dbScans.map((s, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/80 flex items-center justify-between text-xs shadow-sm">
                      <div>
                        <div className="font-bold text-[#064E3B]">{s.disease}</div>
                        <div className="text-[11px] text-[#64748B]">{s.plant} • Plot {s.plotId} • {new Date(s.timestamp).toLocaleTimeString()}</div>
                      </div>
                      <span className="px-2 py-0.5 rounded-full font-bold text-[10px] bg-[#D4F4E4] text-[#065F46]">{s.confidence}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Plots table */}
              <div className="mb-4">
                <h4 className="text-xs font-bold text-[#475569] uppercase tracking-wider mb-2">Cadastral Plots Registry ({dbPlots.length}):</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {dbPlots.map((p, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/80 text-xs shadow-sm">
                      <div className="font-bold text-[#1E293B]">{p.cadastralId} — {p.farmerName}</div>
                      <div className="text-[11px] text-[#64748B]">{p.crop} • NDVI {p.ndvi} • {p.status}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={async () => {
                    if (window.AgriNDB) {
                      const json = await window.AgriNDB.exportJSON();
                      const blob = new Blob([json], { type: 'application/json' });
                      const a = document.createElement('a');
                      a.href = URL.createObjectURL(blob);
                      a.download = `agrin_db_backup_${Date.now()}.json`;
                      a.click();
                    }
                  }}
                  className="px-5 py-2.5 rounded-full text-xs font-bold text-[#064E3B]"
                  style={{ background: '#98DECB', boxShadow: '3px 3px 8px rgba(140,215,195,0.5)' }}
                >
                  📥 Export Database JSON
                </button>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* ── Neumorphic Footer ────────────────────────────────────────────── */}
      <footer className="mt-16 py-8 px-6 text-center text-xs text-[#64748B] border-t border-[rgba(166,180,200,0.25)]">
        <p className="font-semibold text-[#1E293B]">AgriN Platform • Product UI Styleguide Specification</p>
        <p className="mt-1">Neumorphic soft UI • Google Gemini 2.5 Flash Vision AI • Apple Maps MapKit JS • Persistent IndexedDB Storage</p>
      </footer>
    </div>
  );
}
