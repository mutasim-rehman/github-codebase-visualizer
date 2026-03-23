import { useState } from 'react';
import './index.css';

import type { AppData, FileNode } from './types';
import Landing from './components/Landing';
import LoadingScreen from './components/LoadingScreen';
import Sidebar from './components/Sidebar';
import Overview from './components/Overview';
import FileDashboard from './components/Dashboard';
import DiagramsView from './components/DiagramsView';
import { RefreshCw, LayoutDashboard, Network } from 'lucide-react';

const API_BASE = 'http://localhost:5000';

type AppScreen = 'landing' | 'loading' | 'dashboard' | 'error';
type MainView = 'overview' | 'diagrams';

interface DashboardState {
  url: string;
  data: AppData;
}

export default function App() {
  const [screen, setScreen] = useState<AppScreen>('landing');
  const [loadingUrl, setLoadingUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [dash, setDash] = useState<DashboardState | null>(null);

  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [mainView, setMainView] = useState<MainView>('overview');

  const analyze = async (url: string) => {
    setScreen('loading');
    setLoadingUrl(url);
    setSelectedFile(null);
    setMainView('overview');

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const json = await res.json();

      if (!res.ok || json.error) {
        setErrorMsg(json.error ?? `Server error ${res.status}`);
        setScreen('error');
        return;
      }

      setDash({ url, data: json as AppData });
      setScreen('dashboard');
    } catch (e: unknown) {
      setErrorMsg(
        e instanceof Error
          ? `Could not reach API server: ${e.message}`
          : 'Unknown network error'
      );
      setScreen('error');
    }
  };

  const reset = () => {
    setScreen('landing');
    setSelectedFile(null);
    setDash(null);
  };

  const handleSelectFile = (f: FileNode) => {
    setSelectedFile(f);
    setMainView('overview'); // Switch out of diagrams view when a file is selected
  };

  if (screen === 'landing') return <Landing onAnalyze={analyze} />;
  if (screen === 'loading') return <LoadingScreen url={loadingUrl} />;

  if (screen === 'error') {
    return (
      <div className="loading-screen">
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
        <div className="loading-title">Analysis Failed</div>
        <div className="loading-subtitle" style={{ maxWidth: 480, textAlign: 'center' }}>{errorMsg}</div>
        <button className="landing-btn" style={{ marginTop: '1.5rem' }} onClick={reset}>
          <RefreshCw size={14} /> Try Another Repo
        </button>
      </div>
    );
  }

  if (!dash) return null;

  const { url, data } = dash;
  const repoName = url.replace('https://github.com/', '').split('/').slice(0, 2).join('/');

  // Decide what to show in main content
  const showFileDash = !!selectedFile;
  const showDiagrams = !showFileDash && mainView === 'diagrams';
  const showOverview = !showFileDash && mainView === 'overview';

  return (
    <div className="app-shell">
      {/* Top Bar */}
      <header className="topbar">
        <div className="topbar-logo">
          <div className="topbar-logo-icon">🔍</div>
          Codebase Visualizer
        </div>

        {/* Nav tabs */}
        <nav className="topbar-nav">
          <button
            className={`topbar-tab${showOverview || showFileDash ? ' active' : ''}`}
            onClick={() => { setMainView('overview'); setSelectedFile(null); }}
            id="nav-overview"
          >
            <LayoutDashboard size={13} />
            Overview
          </button>
          <button
            className={`topbar-tab${showDiagrams ? ' active' : ''}`}
            onClick={() => { setMainView('diagrams'); setSelectedFile(null); }}
            id="nav-diagrams"
          >
            <Network size={13} />
            Diagrams
          </button>
        </nav>

        <div className="topbar-url">
          <span style={{ color: 'var(--text-muted)', marginRight: 6 }}>analyzing</span>
          {repoName}
        </div>
        <button className="topbar-new-btn" onClick={reset} id="new-analysis-btn">
          <RefreshCw size={13} /> New Analysis
        </button>
      </header>

      <div className="app-body">
        <Sidebar
          data={data}
          selected={selectedFile}
          onSelect={handleSelectFile}
        />

        <main className="main-content">
          {showFileDash && <FileDashboard key={selectedFile!.path} file={selectedFile!} />}
          {showDiagrams && <DiagramsView data={data} />}
          {showOverview && <Overview data={data} onSelectFile={handleSelectFile} />}
        </main>
      </div>
    </div>
  );
}
