import React, { useState, useEffect } from 'react';
import './App.css';
import { db, ref, set, onValue, get } from './firebase';

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const [config, setConfig] = useState({
    maintenance: false,
    version: "1.0.5",
    download_url: "https://github.com/amarb7047/n8gtools/releases/download/v1.0.0/N8GTools_Setup.exe",
    maintenance_msg: "N8 G Tools servers are currently undergoing upgrades. We will be back shortly!"
  });

  // Listen to configuration state from Firebase in real-time
  useEffect(() => {
    const configRef = ref(db, 'config');
    const unsubscribe = onValue(configRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        setConfig(data);
      } else {
        // Initialize default config if database is empty
        set(configRef, {
          maintenance: false,
          version: "1.0.5",
          download_url: "https://github.com/amarb7047/n8gtools/releases/download/v1.0.0/N8GTools_Setup.exe",
          maintenance_msg: "N8 G Tools servers are currently undergoing upgrades. We will be back shortly!"
        });
      }
    });

    return () => unsubscribe();
  }, []);

  // Path routing change listener
  const navigateTo = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };



  if (currentPath === '/admin' || currentPath === '/admin/') {
    return <AdminPanel onNavigate={navigateTo} config={config} />;
  }

  return <LandingPage onNavigate={navigateTo} config={config} />;
}

// ----------------------------------------------------
// PUBLIC LANDING PAGE COMPONENT
// ----------------------------------------------------
function LandingPage({ config }) {
  useEffect(() => {
    // Increment Page Views in Firebase
    const viewsRef = ref(db, 'stats/views');
    get(viewsRef).then((snapshot) => {
      const currentViews = snapshot.val() || 0;
      set(viewsRef, currentViews + 1);
    });
  }, []);

  const handleDownloadClick = () => {
    // Increment Downloads in Firebase
    const downloadsRef = ref(db, 'stats/downloads');
    get(downloadsRef).then((snapshot) => {
      const currentDownloads = snapshot.val() || 0;
      set(downloadsRef, currentDownloads + 1);
    });

    // Capture user geolocation log in Firebase Realtime Database
    fetch('https://ipapi.co/json/')
      .then((res) => res.json())
      .then((data) => {
        const logId = Date.now();
        set(ref(db, `download_logs/${logId}`), {
          timestamp: new Date().toLocaleString(),
          ip: data.ip || 'Unknown IP',
          city: data.city || 'Unknown City',
          country: data.country_name || 'Unknown Country',
          flag: data.country_code ? `https://flagcdn.com/16x12/${data.country_code.toLowerCase()}.png` : ''
        });
      })
      .catch(() => {
        const logId = Date.now();
        set(ref(db, `download_logs/${logId}`), {
          timestamp: new Date().toLocaleString(),
          ip: 'Private IP / VPN',
          city: 'Unknown',
          country: 'Local Network',
          flag: ''
        });
      });
  };

  return (
    <>
      {/* Navigation - Developer Admin Button Removed for Security */}
      <header className="navbar">
        <div className="nav-container">
          <div className="nav-brand">
            <img src="logo.png" alt="N8 Logo" className="nav-logo" />
            <span className="nav-title">N8 G Tools</span>
          </div>
          <nav className="nav-links">
            <a href="#features">Features</a>
            <a href="#booster">Game Booster</a>
            <a href="#diagnostics">Diagnostics</a>
            <a 
              href={config.download_url} 
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleDownloadClick} 
              className="nav-btn-primary"
            >
              Download Setup
            </a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-wrapper">
          <div className="hero-content">
            <div className="badge">🔥 Next-Gen Ultra Mirroring</div>
            <h1>N8 G Tools, Your Ultimate Mirroring & Recording Expert</h1>
            <p className="subtitle">
              All-in-one lag-free mirroring for Android & iOS. Cast in 2K/4K resolution at 120 FPS, record gameplay losslessly, boost CPU/RAM priorities, and monitor diagnostics in real-time.
            </p>
            
            <div className="download-container">
              <a 
                href={config.download_url} 
                target="_blank"
                rel="noopener noreferrer"
                onClick={handleDownloadClick} 
                className="download-btn"
              >
                <span className="btn-icon">📥</span>
                <span className="btn-text">
                  <strong>Download Setup Wizard</strong>
                  <small>Version {config.version} (Stable Edition)</small>
                </span>
              </a>
            </div>
            <p className="specs-info">Supports Windows 10 / 11 (64-bit) | Zero Mobile Lag</p>
          </div>
          
          <div className="hero-visual">
            <div className="visual-card">
              <img src="logo.png" alt="N8 G Tools 3D Logo" className="rotating-logo" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="features-section">
        <div className="section-wrapper">
          <div className="section-header">
            <h2>Zero Blind Spots, Premium Performance</h2>
            <p>Custom-built for pro streamers and mobile gaming content creators.</p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card cyan-glow">
              <div className="card-icon">⚡</div>
              <h3>Ultra Low Latency</h3>
              <p>Direct hardware-accelerated casting pipelines deliver near 0ms video latency over USB and Wi-Fi.</p>
            </div>

            <div className="feature-card emerald-glow">
              <div className="card-icon">🎮</div>
              <h3>120 FPS Gaming</h3>
              <p>Bypasses default refresh rate limits. Cast and record at 60 FPS, 90 FPS, or 120 FPS for absolute smoothness.</p>
            </div>

            <div className="feature-card purple-glow">
              <div className="card-icon">🖥️</div>
              <h3>2K & 4K Mirroring</h3>
              <p>Unlock crystal clear display options. Run streams in native aspect ratios, custom resolutions, and high bitrates.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Game Booster Section */}
      <section id="booster" className="split-section booster-bg">
        <div className="split-wrapper">
          <div className="split-content">
            <div className="badge bg-emerald">🚀 performance optimizer</div>
            <h2>Real-Time Safe Game Booster</h2>
            <p>
              Maximize PC gaming resources with one-click background optimization. Our booster sets CPU priorities of OBS Studio and active device mirrors to high, freeing unused RAM and switching Windows to the Ultimate Performance power scheme.
            </p>
            <ul className="check-list">
              <li>✓ Zero Stream Disconnections: Running mirrors and OBS remain active.</li>
              <li>✓ Permanent Cache Cleaner: Bypasses Windows Recycle Bin.</li>
              <li>✓ CPU Priority Tuning: Allocates maximum resources to streaming tools.</li>
            </ul>
          </div>
          <div className="split-visual">
            <div className="booster-ui-mockup">
              <div className="mockup-header">
                <span className="dot red"></span><span className="dot yellow"></span><span className="dot green"></span>
                <span>N8 Gamer Booster</span>
              </div>
              <div className="mockup-body">
                <div className="booster-circle">BOOST</div>
                <div className="mockup-progress">
                  <div className="progress-fill" style={{ width: '100%' }}></div>
                </div>
                <p className="mockup-status">System Optimized: 154 Cache Files Cleared</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* System Diagnostics Section */}
      <section id="diagnostics" className="split-section diagnostics-bg">
        <div className="split-wrapper reverse">
          <div className="split-content">
            <div className="badge bg-purple">📊 real-time diagnostics</div>
            <h2>Circular System Info Monitor</h2>
            <p>
              Get instant feedback on your PC's health inside the application. View real-time animated circular progress gauges for CPU, RAM, and Disk space, coupled with hardware metrics and operating system details.
            </p>
            <ul className="check-list">
              <li>✓ High Precision: Instantaneous system load monitoring.</li>
              <li>✓ Hardware Details: Displays CPU processor model and RAM capacity.</li>
              <li>✓ Elegant Neon Design: Fits perfectly into modern dark stream setups.</li>
            </ul>
          </div>
          <div className="split-visual">
            <div className="diagnostics-ui-mockup">
              <div className="gauge-box">
                <div className="gauge cyan"><span>12%</span><small>CPU</small></div>
                <div className="gauge emerald"><span>48%</span><small>RAM</small></div>
                <div className="gauge orange"><span>76%</span><small>Disk</small></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <div className="footer-brand">
            <img src="logo.png" alt="N8 G Tools Logo" className="footer-logo" />
            <span>N8 G Tools</span>
          </div>
          <p>© 2026 N8 Gamer. All rights reserved. Developed for mobile streamers.</p>
        </div>
      </footer>
    </>
  );
}

// ----------------------------------------------------
// DEVELOPER CONTROL PANEL COMPONENT WITH SECURE PIN
// ----------------------------------------------------
function AdminPanel({ onNavigate, config }) {
  const [pin, setPin] = useState('');
  const [isAuthorized, setIsAuthorized] = useState(
    sessionStorage.getItem('n8g_auth') === 'true'
  );
  
  const [views, setViews] = useState(0);
  const [downloads, setDownloads] = useState(0);
  const [logs, setLogs] = useState([]);
  
  const [maint, setMaint] = useState(config.maintenance);
  const [version, setVersion] = useState(config.version);
  const [dlUrl, setDlUrl] = useState(config.download_url);
  const [maintMsg, setMaintMsg] = useState(config.maintenance_msg || "");

  // Sync state values when global configuration updates
  useEffect(() => {
    setMaint(config.maintenance);
    setVersion(config.version);
    setDlUrl(config.download_url);
    setMaintMsg(config.maintenance_msg || "");
  }, [config]);

  // Load telemetry logs and statistics from Firebase Database
  useEffect(() => {
    if (!isAuthorized) return;

    // 1. Listen to Stats
    const statsRef = ref(db, 'stats');
    const unsubStats = onValue(statsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        setViews(data.views || 0);
        setDownloads(data.downloads || 0);
      }
    });

    // 2. Listen to Geolocation logs
    const logsRef = ref(db, 'download_logs');
    const unsubLogs = onValue(logsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        // Sort logs descending by timestamp
        const logsList = Object.keys(data).map(key => data[key]);
        logsList.reverse();
        setLogs(logsList);
      } else {
        setLogs([]);
      }
    });

    return () => {
      unsubStats();
      unsubLogs();
    };
  }, [isAuthorized]);

  const handleLogin = (e) => {
    e.preventDefault();
    if (pin === '741163') {
      setIsAuthorized(true);
      sessionStorage.setItem('n8g_auth', 'true');
    } else {
      alert('Access Denied: Incorrect Developer PIN Code.');
      setPin('');
    }
  };

  const handleConfigSave = () => {
    set(ref(db, 'config'), {
      maintenance: maint,
      version: version,
      download_url: dlUrl,
      maintenance_msg: maintMsg
    }).then(() => {
      alert('Firebase Database configurations successfully updated!');
    });
  };

  const handleResetStats = () => {
    if (confirm('Clear page views, downloads counter, and all download activity logs in Firebase Realtime Database?')) {
      set(ref(db, 'stats'), { views: 0, downloads: 0 });
      set(ref(db, 'download_logs'), null);
    }
  };

  const conversion = views > 0 ? ((downloads / views) * 100).toFixed(1) : '0.0';

  // Authorization lock screen (Rendered if not logged in)
  if (!isAuthorized) {
    return (
      <div className="maintenance-body">
        <form onSubmit={handleLogin} className="maintenance-screen" style={{ maxWidth: '400px' }}>
          <span className="maint-icon" style={{ animation: 'none' }}>🔒</span>
          <h2 style={{ marginBottom: '10px' }}>Developer Access</h2>
          <p style={{ marginBottom: '25px' }}>Enter the 6-digit pin code to unlock the admin telemetry dashboard.</p>
          
          <div className="form-group" style={{ textAlign: 'left' }}>
            <input 
              type="password" 
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="Enter PIN Code" 
              maxLength="6"
              style={{ textAlign: 'center', fontSize: '20px', letterSpacing: '4px', padding: '15px' }}
              autoFocus
            />
          </div>
          
          <button type="submit" className="nav-btn-primary" style={{ width: '100%', border: 'none', padding: '14px', cursor: 'pointer', marginTop: '10px' }}>
            Unlock Dashboard
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="admin-body">
      <header className="navbar">
        <div className="nav-container">
          <div className="nav-brand">
            <img src="logo.png" alt="Logo" className="nav-logo" />
            <span className="nav-title">N8 Developer Console</span>
          </div>
          <nav className="nav-links">
            <button onClick={() => onNavigate('/')} className="nav-btn-secondary">← Back to Site</button>
            <button onClick={handleResetStats} className="nav-btn-secondary" style={{ borderColor: 'var(--red)', color: 'var(--red)' }}>Reset Telemetry</button>
          </nav>
        </div>
      </header>

      <main className="admin-container">
        <div className="badge bg-purple">⚙️ Database Controller</div>
        <h2 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '32px', marginBottom: '25px', color: 'white' }}>Global Controls & Updates</h2>

        {/* Configurations Card */}
        <div className="control-card">
          <h3 style={{ fontFamily: 'Space Grotesk, sans-serif', color: 'white', marginBottom: '20px', fontSize: '20px' }}>Windows App & Server State</h3>
          
          <div className="switch-container">
            <div className="switch-label">
              <strong>Server Maintenance Mode</strong>
              <span>Blocks public landing site and locks desktop application consoles.</span>
            </div>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={maint} 
                onChange={(e) => setMaint(e.target.checked)} 
              />
              <span className="slider"></span>
            </label>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
            <div className="form-group">
              <label>Target Version (Updates Check)</label>
              <input 
                type="text" 
                value={version} 
                onChange={(e) => setVersion(e.target.value)} 
                placeholder="e.g. 1.0.1" 
              />
            </div>
            <div className="form-group">
              <label>Download Package Source URL</label>
              <input 
                type="text" 
                value={dlUrl} 
                onChange={(e) => setDlUrl(e.target.value)} 
                placeholder="e.g. N8GTools_Setup.exe" 
              />
            </div>
            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label>Custom Maintenance Overlay Message</label>
              <input 
                type="text" 
                value={maintMsg} 
                onChange={(e) => setMaintMsg(e.target.value)} 
                placeholder="e.g. Server upgrade in progress. Back online in 30 minutes!" 
              />
            </div>
          </div>
          
          <button onClick={handleConfigSave} className="nav-btn-primary" style={{ marginTop: '15px', border: 'none', padding: '12px 25px', cursor: 'pointer' }}>
            Save Configurations
          </button>
        </div>

        {/* Stats Grid */}
        <div className="badge bg-emerald">📈 Telemetry Statistics</div>
        <div className="stats-grid" style={{ marginTop: '15px' }}>
          <div className="stat-card cyan-glow">
            <div className="stat-icon">👁️</div>
            <div className="stat-info">
              <span className="stat-title">Total Page Views</span>
              <h3>{views.toLocaleString()}</h3>
            </div>
          </div>

          <div className="stat-card emerald-glow">
            <div className="stat-icon">📥</div>
            <div className="stat-info">
              <span className="stat-title">Total Downloads</span>
              <h3>{downloads.toLocaleString()}</h3>
            </div>
          </div>

          <div className="stat-card purple-glow">
            <div className="stat-icon">📈</div>
            <div className="stat-info">
              <span className="stat-title">Conversion Rate</span>
              <h3>{conversion}%</h3>
            </div>
          </div>
        </div>

        {/* Geolocation Table Log */}
        <div className="log-section">
          <h3 style={{ fontFamily: 'Space Grotesk, sans-serif', color: 'white', marginBottom: '20px', fontSize: '22px' }}>Recent Download Logs (Live Geolocation)</h3>
          <div className="table-container">
            <table className="log-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>IP Address</th>
                  <th>Location</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center', color: '#8E9AAF', padding: '30px' }}>No download activity recorded yet.</td>
                  </tr>
                ) : (
                  logs.map((log, i) => (
                    <tr key={i}>
                      <td style={{ color: '#66FCF1', fontWeight: 600 }}>{log.timestamp}</td>
                      <td style={{ fontFamily: 'monospace' }}>{log.ip}</td>
                      <td>
                        {log.flag ? (
                          <img src={log.flag} alt="flag" style={{ verticalAlign: 'middle', marginRight: '8px', borderRadius: '2px' }} />
                        ) : '🌍 '}
                        {log.city}, {log.country}
                      </td>
                      <td><span className="status-badge">Completed</span></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

// ----------------------------------------------------
// SERVER MAINTENANCE LOCK OVERLAY COMPONENT
// ----------------------------------------------------
function MaintenanceScreen({ message }) {
  return (
    <div className="maintenance-body">
      <div className="maintenance-screen">
        <span className="maint-icon">⚙️</span>
        <h2>Server Maintenance Active</h2>
        <p>{message || "N8 G Tools servers are currently undergoing upgrades. We will be back shortly!"}</p>
        <div className="booster-circle" style={{ borderColor: 'var(--cyan)', color: 'var(--cyan)', margin: '25px auto 0 auto', width: '80px', height: '80px', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', fontWeight: 'bold', fontSize: '11px' }}>
          UPGRADE
        </div>
      </div>
    </div>
  );
}
