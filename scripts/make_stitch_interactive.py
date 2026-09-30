import os
import glob
import re

base_dir = r"C:\Users\somya\Downloads\codeforcomm\AgriN\dashboard\public\stitch"
html_files = glob.glob(os.path.join(base_dir, "*", "code.html"))

ROUTE_MAP = {
    # Mobile routes
    "plots": "/stitch/home_farm_digital_twin/code.html",
    "health": "/stitch/home_farm_digital_twin/code.html",
    "advisories": "/stitch/home_farm_digital_twin/code.html",
    "scan-ai": "/stitch/crop_disease_doctor/code.html",
    "scan": "/stitch/crop_disease_doctor/code.html",
    "what-if": "/stitch/what_if_simulator/code.html",
    "whatif": "/stitch/what_if_simulator/code.html",
    "sync": "/stitch/offline_mode_data_sync/code.html",
    "offline": "/stitch/offline_mode_data_sync/code.html",
    # Officer routes
    "geospatial-command": "/stitch/geospatial_command_triage_drawer/code.html",
    "geospatial": "/stitch/geospatial_command_triage_drawer/code.html",
    "disease-triage-queue": "/stitch/disease_triage_queue/code.html",
    "triage": "/stitch/disease_triage_queue/code.html",
    "farmer-plot-registry": "/stitch/farmer_plot_management_directory/code.html",
    "registry": "/stitch/farmer_plot_management_directory/code.html",
    "telemetry-weather-stations": "/stitch/telemetry_weather_stations/code.html",
    "weather": "/stitch/telemetry_weather_stations/code.html",
    "api-integration-architecture": "/stitch/backend_api_integration_architecture/code.html",
    "api": "/stitch/backend_api_integration_architecture/code.html",
}

INTERACTIVE_INJECTION = """
<!-- AgriN Universal Interactive Runtime Layer -->
<div id="agrin-toast-container" style="position: fixed; top: 20px; right: 20px; z-index: 999999; display: flex; flex-direction: column; gap: 8px; pointer-events: none;"></div>

<script>
(function() {
  console.log('[AgriN] Interactive runtime active.');

  // Toast System
  window.showAgriToast = function(message, type = 'success') {
    const container = document.getElementById('agrin-toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.style.cssText = 'pointer-events: auto; padding: 12px 18px; border-radius: 12px; font-family: Inter, sans-serif; font-size: 13px; font-weight: 600; color: #fff; display: flex; items-center; gap: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); transition: all 0.3s ease; transform: translateY(-10px); opacity: 0;';
    
    if (type === 'success') {
      toast.style.backgroundColor = '#006948';
      toast.style.border = '1px solid #68dba9';
      toast.innerHTML = '<span>✅ ' + message + '</span>';
    } else if (type === 'warn') {
      toast.style.backgroundColor = '#904d00';
      toast.style.border = '1px solid #fe932c';
      toast.innerHTML = '<span>⚠️ ' + message + '</span>';
    } else {
      toast.style.backgroundColor = '#131b2e';
      toast.style.border = '1px solid #3d4a42';
      toast.innerHTML = '<span>ℹ️ ' + message + '</span>';
    }

    container.appendChild(toast);
    requestAnimationFrame(() => {
      toast.style.transform = 'translateY(0)';
      toast.style.opacity = '1';
    });

    setTimeout(() => {
      toast.style.transform = 'translateY(-10px)';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  };

  // Web Speech API Voice Synthesis
  window.speakAgriVoice = function(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
      showAgriToast('Playing voice advisory via Web Speech audio...', 'info');
    } else {
      showAgriToast('Audio synthesized: ' + text.slice(0, 50) + '...', 'info');
    }
  };

  // Wire up all navigation links
  document.addEventListener('DOMContentLoaded', function() {
    const routeMap = """ + str(ROUTE_MAP) + """;

    document.querySelectorAll('a, button').forEach(el => {
      const path = el.getAttribute('data-path');
      const href = el.getAttribute('href');
      const text = el.innerText ? el.innerText.trim().toLowerCase() : '';

      // Fix navigation paths
      if (path && routeMap[path]) {
        el.setAttribute('href', routeMap[path]);
        el.addEventListener('click', function(e) {
          e.preventDefault();
          window.location.href = routeMap[path];
        });
      } else if (href === '#' || !href) {
        if (text.includes('disease triage') || text.includes('triage queue')) {
          el.onclick = () => window.location.href = routeMap['disease-triage-queue'];
        } else if (text.includes('farmer') && text.includes('plot')) {
          el.onclick = () => window.location.href = routeMap['farmer-plot-registry'];
        } else if (text.includes('geospatial') || text.includes('command')) {
          el.onclick = () => window.location.href = routeMap['geospatial-command'];
        } else if (text.includes('weather') || text.includes('telemetry')) {
          el.onclick = () => window.location.href = routeMap['telemetry-weather-stations'];
        } else if (text.includes('api') || text.includes('architecture')) {
          el.onclick = () => window.location.href = routeMap['api-integration-architecture'];
        } else if (text.includes('scan')) {
          el.onclick = () => window.location.href = routeMap['scan-ai'];
        } else if (text.includes('what-if') || text.includes('what if')) {
          el.onclick = () => window.location.href = routeMap['what-if'];
        } else if (text.includes('sync') || text.includes('offline')) {
          el.onclick = () => window.location.href = routeMap['sync'];
        }
      }

      // Action button listeners
      if (text.includes('broadcast push') || text.includes('broadcast advisory')) {
        el.onclick = (e) => {
          e.preventDefault();
          showAgriToast('Advisory broadcasted to Ramesh Patel via WhatsApp & SMS (Twilio gateway)!', 'success');
        };
      } else if (text.includes('trigger drone scan')) {
        el.onclick = (e) => {
          e.preventDefault();
          showAgriToast('Multispectral drone flight dispatched to Sector 4B (Altitude: 45m).', 'info');
        };
      } else if (text.includes('confirm diagnosis') || text.includes('approve prescription')) {
        el.onclick = (e) => {
          e.preventDefault();
          el.innerText = '✅ Confirmed by Officer';
          el.style.backgroundColor = '#006948';
          el.style.color = '#fff';
          showAgriToast('Diagnosis confirmed! Prescription locked and synced to farmer digital twin.', 'success');
        };
      } else if (text.includes('override') || text.includes('reclassify')) {
        el.onclick = (e) => {
          e.preventDefault();
          el.innerText = '⚠️ Overridden';
          el.style.backgroundColor = '#904d00';
          el.style.color = '#fff';
          showAgriToast('Disease classification overridden by Extension Officer.', 'warn');
        };
      } else if (text.includes('listen audio') || text.includes('voice memo') || el.title?.includes('Voice')) {
        el.onclick = (e) => {
          e.preventDefault();
          speakAgriVoice("Namaste Ramesh Patel. Crop health NDVI is zero point seven four. Reduce midday furrow evaporation. Apply preventive copper fungicide spray on Sector C due to high canopy humidity.");
        };
      } else if (text.includes('sync') && (text.includes('force') || text.includes('now') || text.includes('telemetry'))) {
        el.onclick = (e) => {
          e.preventDefault();
          showAgriToast('Syncing with AgriN Cloud & Sentinel-2 multispectral pipeline...', 'info');
          setTimeout(() => {
            showAgriToast('Sync Complete! 7,841 plots and 3 offline submissions updated.', 'success');
          }, 1200);
        };
      }
    });

    // Make map SVG / polygon elements clickable
    document.querySelectorAll('polygon, path').forEach(poly => {
      poly.style.cursor = 'pointer';
      poly.addEventListener('click', function() {
        showAgriToast('Plot Selected: Cadastral Sector 4B (Sonalika Wheat PBW-502). NDVI: 0.74, Moisture: 24.8%.', 'info');
      });
    });
  });
})();
</script>
"""

count = 0
for filepath in html_files:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Remove previous injection if any
    content = re.sub(
        r"<!-- AgriN Universal Interactive Runtime Layer -->.*?<\/script>",
        "",
        content,
        flags=re.DOTALL,
    )

    # Inject right before </body>
    if "</body>" in content:
        content = content.replace("</body>", INTERACTIVE_INJECTION + "\n</body>")
    else:
        content += INTERACTIVE_INJECTION

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    count += 1
    print(f"Enhanced: {os.path.basename(os.path.dirname(filepath))}")

print(f"Successfully injected interactive runtime into {count} screens!")
