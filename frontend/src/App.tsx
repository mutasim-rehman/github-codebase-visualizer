import { useState } from 'react';
import './index.css';

import type { AppData, FileNode } from './types';
import Landing from './components/Landing';
import LoadingScreen from './components/LoadingScreen';
import Sidebar from './components/Sidebar';
import Overview from './components/Overview';
import FileDashboard from './components/Dashboard';
import { RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:5000';

type AppState =
  | { screen: 'landing' }
  | { screen: 'loading'; url: string }
  | { screen: 'dashboard'; url: string; data: AppData }
  | { screen: 'error'; url: string; message: string };

export default function App() {
  const [state, setState] = useState<AppState>({ screen: 'landing' });
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);

  const analyze = async (url: string) => {
    setState({ screen: 'loading', url });
    setSelectedFile(null);

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const json = await res.json();

      if (!res.ok || json.error) {
        setState({ screen: 'error', url, message: json.error ?? `Server error ${res.status}` });
        return;
      }

      setState({ screen: 'dashboard', url, data: json as AppData });
    } catch (e: unknown) {
      setState({
        screen: 'error',
        url,
        message: e instanceof Error
          ? `Could not reach API server: ${e.message}`
          : 'Unknown network error',
      });
    }
  };

  const reset = () => {
    setState({ screen: 'landing' });
    setSelectedFile(null);
  };

  if (state.screen === 'landing') return <Landing onAnalyze={analyze} />;
  if (state.screen === 'loading') return <LoadingScreen url={state.url} />;

  if (state.screen === 'error') {
    return (
      <div className="loading-screen">
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
        <div className="loading-title">Analysis Failed</div>
        <div className="loading-subtitle" style={{ maxWidth: 480, textAlign: 'center' }}>{state.message}</div>
        <button
          className="landing-btn"
          style={{ marginTop: '1.5rem' }}
          onClick={reset}
        >
          <RefreshCw size={14} /> Try Another Repo
        </button>
      </div>
    );
  }

  // Dashboard
  const { url, data } = state;
  const repoName = url.replace('https://github.com/', '').split('/').slice(0, 2).join('/');

  return (
    <div className="app-shell">
      {/* Top Bar */}
      <header className="topbar">
        <div className="topbar-logo">
          <div className="topbar-logo-icon">🔍</div>
          Codebase Visualizer
        </div>
        <div className="topbar-url">
          <span style={{ color: 'var(--text-muted)', marginRight: 6 }}>analyzing</span>
          {repoName}
        </div>
        <button className="topbar-new-btn" onClick={reset} id="new-analysis-btn">
          <RefreshCw size={13} /> New Analysis
        </button>
      </header>

      <div className="app-body">
        <Sidebar data={data} selected={selectedFile} onSelect={setSelectedFile} />

        <main className="main-content">
          {selectedFile
            ? <FileDashboard key={selectedFile.path} file={selectedFile} />
            : <Overview data={data} onSelectFile={setSelectedFile} />
          }
        </main>
      </div>
    </div>
  );
}
