# N8 G Tools – Next-Gen Screen Mirroring & Game Optimizer

N8 G Tools is an enterprise-grade utility suite built for mobile gaming content creators, streamers, and developers. It provides zero-lag screen casting, high frame-rate mirroring, audio controls, a performance booster, and telemetry diagnostics.

---

## ⚡ Key Features

### 🖥️ Ultra Low Latency Screen Mirroring
*   **Android Mirroring:** Built on a customized `scrcpy` engine wrapper. Stream in 2K/4K resolution at 60 FPS, 90 FPS, or 120 FPS.
*   **iOS Mirroring:** Uses a hardware-accelerated `uxplay` (AirPlay) protocol server. Directly mirror iPad or iPhone screen feed to your Windows desktop over Wi-Fi/USB.
*   **Audio Redirection:** Mute/unmute mirroring stream audio, redirect to virtual sound cards, and record losslessly.
*   **Full Screen Mode:** Toggle F11 or click `Full Screen` to hide borders and maximize game feeds for native streaming canvas sizing.

### 🚀 Real-Time Safe Game Booster
*   **Priority Tuning:** Automatically adjusts CPU priority tables of OBS Studio and mirroring window tasks to High.
*   **Cache Cleaner:** One-click junk cache cleaning that bypasses Windows Recycle Bin for instantaneous disk speed optimization.
*   **Power Plans:** Switches active Windows power schemes to Ultimate Performance.
*   *Safety:* Protects active stream sessions and ensures game disconnections do not occur.

### 📊 Circular Diagnostics Dials
*   **Dashboard Gauges:** Real-time animated circular progress meters for CPU utilization, RAM consumption, and System Storage.
*   **Metadata Console:** Lists operating system versions, CPU processor names, and installed memory capacity.

### 🌐 Cloud Telemetry & Maintenance Control
*   **Vite + React Web App:** Lightweight React landing page and admin portal.
*   **Secure Authorization:** Developer dashboard protected with a custom 6-digit PIN screen (`741163`).
*   **Live Geolocation Analytics:** Real-time database logging of visitors (views, downloads conversion, and IP/Country mapping using flag APIs).
*   **Maintenance Toggle:** Locks both the live website and the desktop app with an animated "System Upgrades in Progress" block screen when server upgrades are turned ON.

---

## 📁 Repository Structure

```
├── website/              # Vite + React web application source code
├── core/                 # Mirror engines runners, download managers, and hardware monitor
├── ui/                   # PyQt5 tabs and main window interfaces
├── main.py               # Desktop application entry point
├── setup_wizard.py       # Win32 install installer wizard GUI
├── N8GTools.spec         # PyInstaller compilation specifications
└── README.md             # Project documentation
```

---

## 🛠️ Local Development & Setup

### Requirements
*   Python 3.10+
*   Node.js 18+ (for Web App)
*   Git

### Desktop App Setup
1. Install dependencies:
   ```bash
   pip install PyQt5 requests psutil pywin32
   ```
2. Start application:
   ```bash
   python main.py
   ```

### Web App Setup
1. Install dependencies:
   ```bash
   cd website
   npm install
   ```
2. Run development server:
   ```bash
   npm run dev
   ```
3. Compile production bundle:
   ```bash
   npm run build
   ```

---

## 🚀 Deployed Telemetry Architecture

The system uses **Firebase Realtime Database** to synchronize data between the web client and the Windows application in real-time.
*   **Database Endpoint:** `https://n8-g-tools-default-rtdb.asia-southeast1.firebasedatabase.app`
*   **Hosting Site:** `https://n8-g-tools.web.app`

Developed with ❤️ for the N8 Gamer community. All rights reserved.
