"""
Automated recording script for AgriN Hackathon Submission Demo Video.
Uses Playwright to capture high-definition, beautifully paced interactions across:
1. AgriN Mobile Farmer Assistant (Digital Twin, Gemini Vision AI, BRICS Switcher, Regen AI, What-If Simulator, Offline Sync)
2. AgriN Extension Officer Command Portal & Digital Public Good Architecture
Generates WebM and MP4 video files in demo_video/ directory.
"""

import os
import sys
import time
import glob
from pathlib import Path

# Force UTF-8 stdout for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "demo_video"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def record_agrin_demo():
    print(f"🎬 Starting AgriN Demo Video Recording...")
    print(f"📁 Output Directory: {OUTPUT_DIR}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--font-render-hinting=none"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1280, "height": 720}
        )

        page = context.new_page()

        # ── SCENE 1: Mobile Farmer Assistant ────────────────────────────────
        print("📱 Scene 1: AgriN Mobile Farmer Assistant...")
        page.goto("http://127.0.0.1:5173/mobile/index.html", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 1. BRICS Country Switcher Demonstration
        print("🌍 Demonstrating BRICS Agro-Climatic Cooperation...")
        page.select_option("#brics-country-select", "BR")
        page.wait_for_timeout(2000)

        page.select_option("#brics-country-select", "CN")
        page.wait_for_timeout(2000)

        page.select_option("#brics-country-select", "IN")
        page.wait_for_timeout(2000)

        # 2. Voice Agro-Advisory Playback
        print("🔊 Playing Audio Agro-Advisory...")
        page.click("#btn-play-home-voice")
        page.wait_for_timeout(2500)

        # 3. Crop Disease Doctor (Gemini Vision AI)
        print("🔬 Switching to Crop Disease Doctor...")
        page.click("#tab-scan")
        page.wait_for_timeout(1500)

        print("🍃 Selecting Disease Specimen: Wheat Stripe Rust...")
        page.click("#pill-wheat")
        page.wait_for_timeout(1500)

        print("🌽 Selecting Disease Specimen: Corn Northern Blight...")
        page.click("#pill-corn")
        page.wait_for_timeout(1500)

        print("🍅 Selecting Disease Specimen: Tomato Early Blight...")
        page.click("#pill-tomato")
        page.wait_for_timeout(1500)

        print("⚡ Running Multimodal Pathology Diagnosis with Gemini AI...")
        page.click("#mobile-scan-btn")
        page.wait_for_timeout(3500)

        # 4. Regenerative AI Tab
        print("🌱 Switching to Regenerative AI Recommendations...")
        page.click("#tab-regen")
        page.wait_for_timeout(2000)
        
        # Scroll gently inside view-regen to show all recommended crops
        page.evaluate("document.getElementById('view-regen').scrollTop = 160")
        page.wait_for_timeout(2500)

        # 5. What-If Yield & Climate Simulator
        print("🎛️ Switching to What-If Climate Simulator...")
        page.click("#tab-whatif")
        page.wait_for_timeout(1500)

        print("🌡️ Adjusting Temperature (+4.0°C) and Rainfall (-25%)...")
        page.evaluate("""
            const t = document.getElementById('temp-slider');
            t.value = '4.0';
            const r = document.getElementById('rain-slider');
            r.value = '-25';
            const c = document.getElementById('carbon-slider');
            c.value = '2.2';
            updateWhatIfSimulation();
        """)
        page.wait_for_timeout(2500)

        # 6. Offline Sync & Public Good Mesh
        print("📡 Switching to Offline Sync & Public Good Mesh...")
        page.click("#tab-sync")
        page.wait_for_timeout(1500)

        print("📶 Toggling Offline Field Mode...")
        page.click("#btn-toggle-network")
        page.wait_for_timeout(1500)
        page.click("#btn-toggle-network")
        page.wait_for_timeout(1500)

        print("🔄 Draining Local Queue & Mesh Syncing...")
        page.click("#btn-force-sync")
        page.wait_for_timeout(3000)

        # ── SCENE 2: Extension Officer Command Web Portal ───────────────────
        print("🌐 Scene 2: AgriN Extension Officer Command Portal...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.wait_for_timeout(2500)

        print("📜 Scrolling through Command Center KPIs & Apple Maps GIS...")
        page.evaluate("window.scrollTo({ top: 350, behavior: 'smooth' })")
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo({ top: 750, behavior: 'smooth' })")
        page.wait_for_timeout(2500)

        page.evaluate("window.scrollTo({ top: 1200, behavior: 'smooth' })")
        page.wait_for_timeout(2500)

        page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
        page.wait_for_timeout(2000)

        # Close context to flush video
        print("💾 Finalizing video capture...")
        video = page.video
        context.close()
        browser.close()

        if video:
            video_path = video.path()
            print(f"✅ Raw Video saved at: {video_path}")
            
            # Destination file
            dest_webm = OUTPUT_DIR / "agrin_submission_demo.webm"
            dest_mp4 = OUTPUT_DIR / "agrin_submission_demo.mp4"
            
            # Rename or copy to submission name
            if os.path.exists(video_path):
                import shutil
                shutil.copy(video_path, dest_webm)
                print(f"🎉 WebM Demo Ready: {dest_webm} ({os.path.getsize(dest_webm)} bytes)")

                # Convert to MP4 using OpenCV if available
                try:
                    import cv2
                    print("🎬 Converting WebM to MP4 with OpenCV for universal compatibility...")
                    cap = cv2.VideoCapture(str(dest_webm))
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(str(dest_mp4), fourcc, fps, (w, h))

                    frame_count = 0
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        out.write(frame)
                        frame_count += 1

                    cap.release()
                    out.release()
                    if os.path.exists(dest_mp4) and os.path.getsize(dest_mp4) > 1000:
                        print(f"🎉 MP4 Demo Ready: {dest_mp4} ({os.path.getsize(dest_mp4)} bytes, {frame_count} frames)")
                    else:
                        print("⚠️ MP4 export small, WebM is the primary high-quality submission video.")
                except Exception as ex:
                    print(f"Note on MP4 conversion: {ex}. WebM is ready and valid.")

        print("✨ Demo Video Recording Complete!")

if __name__ == "__main__":
    record_agrin_demo()
