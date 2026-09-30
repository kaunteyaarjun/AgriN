# AgriN — Regenerative Agricultural Intelligence Network

> **BRICS Theme: Cooperation & Sustainable Food Security**  
> *Track 4 — AgriN: Interoperable Digital Agriculture Network for Small & Marginal Farmers*

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.124-teal.svg)](src/)
[![PostgreSQL & PostGIS](https://img.shields.io/badge/Database-Supabase_PostGIS-3ecf8e.svg)](https://supabase.com)
[![React 19](https://img.shields.io/badge/Frontend-React_19_Vite-61dafb.svg)](dashboard/)

---

## 🌾 The Challenge & Problem

Small and marginal farmers across emerging economies lack access to real-time, data-driven agricultural guidance. Relying on outdated traditional guesswork rather than high-resolution satellite imagery, soil health analytics, and hyper-local climate forecasting leads to catastrophic crop failure, degrades fragile topsoil, and threatens global food security. Furthermore, the absence of interoperable digital public infrastructure prevents cross-border collaboration on climate-resilient farming models.

**AgriN** is an open, interoperable digital public good inspired by the BRICS Agricultural Research Platform. It unites satellite telemetry, soil health modeling, generative AI agronomy, and in-field multimodal disease diagnostics into one unified, self-hostable intelligence platform for farmers and extension officers.

---

## 🌟 Key Capabilities

### 1. 🛰️ Satellite Canopy & Farm Digital Twin
- Real-time **Sentinel-2 MSI** and **CBERS-4A** NDVI vegetation indices to track crop vigor, canopy health, and vegetative stress.
- PostGIS-powered cadastral parcels (`geometry(Geometry, 4326)`) enabling precise field boundary analytics and zonal management.
- Soil moisture, canopy relative humidity, and evapotranspiration telemetry matrix.

### 2. 🔬 Gemini Vision AI & PlantVillage Disease Doctor
- Instant leaf pathology triage using **Google Gemini 2.5 Flash Vision** and the **PlantVillage 54,000+ botanical class** knowledge base.
- Identifies critical crop pathogens (e.g., *Early Blight*, *Stripe Rust*, *Northern Corn Leaf Blight*, *Apple Scab*).
- Outputs tri-part advisories:
  - **🚨 Immediate Field Quarantine**: Physical interventions to halt airborne and splash spore transmission.
  - **🌿 Certified Regenerative & Bio-Control**: Organic remedies (*Bacillus subtilis*, cold-pressed Neem, *Trichoderma viride*).
  - **🧪 Standard Chemical IPM**: Formulations, exact dilution ratios, and safety intervals.

### 3. 🌱 Regenerative Crop Planning & Soil Carbon Intelligence
- Soil Health Index tracking **Soil Organic Carbon (SOC %)**, N-P-K nutrient balances, and microbial activity.
- AI-driven cover cropping and crop rotation recommendations (e.g., biological nitrogen fixation via Chickpea, root compaction breakup via deep-rooted Pearl Millet, nematode suppression via Sunn Hemp).

### 4. 🎛️ Climate & Yield Risk What-If Simulator
- Interactive multi-variable scenario modeling: adjust temperature anomalies (-4°C to +6°C), rainfall deviations (-50% to +50%), and regenerative soil carbon buffers (+0% to +3% SOC).
- Dynamic real-time calculation of net projected yield delta (%), economic risk, and pest outbreak probabilities.

### 5. 🌍 BRICS Multi-Nation Cooperation & Agro-Climatic Zones
- Tailored regional crop models and multilingual spoken advisories:
  - 🇮🇳 **India**: Indo-Gangetic Plains, Karnal (Basmati Paddy & Sonalika Wheat)
  - 🇧🇷 **Brazil**: Cerrado Biome, Sorriso Mato Grosso (No-till Soybeans)
  - 🇨🇳 **China**: Songnen Plain, Heilongjiang (Black Soil Maize)
  - 🇷🇺 **Russia**: Kuban Steppe, Krasnodar Krai (Chernozem Winter Wheat)
  - 🇿🇦 **South Africa**: Highveld Plains, Free State (Dryland Sunflower)

### 6. 📡 Offline-First Resilient Architecture & Digital Public Good
- Local-first caching in **IndexedDB** (`agrin-db.js`) allowing rural farmers with zero connectivity to record observations and run diagnostics.
- Automatic background drainage over LoRaWAN mesh networks or cellular re-connection.
- Standardized open data exchange export compatible with OGC and STAC specifications.

---

## 🏗️ Architecture & Technology Stack

```
               ┌────────────────────────────────────────────────────────┐
               │              AgriN Client Interfaces                   │
               │  • React 19 + Vite Extension Officer Command Portal     │
               │  • Mobile Smartphone Assistant (PWA / Offline-first)   │
               └──────────────┬──────────────────────────┬──────────────┘
                              │                          │
                   IndexedDB  │ Offline Mesh             │ REST / WebSockets
                   AgriNDB    ▼                          ▼
               ┌──────────────────────┐        ┌────────────────────────┐
               │ Browser Local Cache  │        │ FastAPI Python Backend │
               │ • PlantVillage Engine│        │ • Modular Monolith     │
               │ • Web Speech TTS     │        │ • Async Domain Routers │
               └──────────────────────┘        └───────────┬────────────┘
                                                           │
                                             SQLAlchemy 2  │ AsyncPG
                                                           ▼
                                      ┌─────────────────────────────────┐
                                      │   Supabase Cloud PostgreSQL     │
                                      │   • PostGIS Spatial Extension   │
                                      │   • Cadastral Polygons (4326)   │
                                      └─────────────────────────────────┘
```

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 Async, Pydantic v2, Alembic migrations.
- **Database**: Cloud PostgreSQL 17 + PostGIS (hosted on Supabase) for vector cadastral parcels and time-series telemetry.
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS, Neumorphic Soft UI Design System.
- **AI & Diagnostics**: Multimodal Google Gemini Vision API + PlantVillage open agronomic taxonomy.

---

## ⚡ Quickstart & Setup

### Prerequisites
- Python 3.12+ (or [uv](https://docs.astral.sh/uv/))
- Node.js 20+ & npm

### 1. Clone & Configure
```bash
git clone https://github.com/kaunteyaarjun/AgriN.git
cd AgriN

# Copy environment template
cp .env.example .env
```

Set your Supabase PostgreSQL connection string in `.env`:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres?ssl=require
```

### 2. Backend Setup
```bash
# Install dependencies
uv sync --extra dev

# Run PostGIS database migrations
uv run alembic upgrade head

# Start FastAPI server (Port 8000)
uv run uvicorn src.main:create_app --factory --port 8000
```
API Documentation will be live at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd dashboard
npm install
npm run dev
```
Open `http://localhost:5173/` for the Extension Portal, or `http://localhost:5173/mobile/index.html` for the Mobile Farmer App.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details. Built as an open digital public good for the BRICS Agricultural Cooperation Initiative.
