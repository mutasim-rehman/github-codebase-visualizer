import { useState, type KeyboardEvent } from 'react';
import { GitBranch, Zap } from 'lucide-react';

interface LandingProps {
  onAnalyze: (url: string) => void;
}

const EXAMPLES = [
  'https://github.com/facebook/react',
  'https://github.com/vercel/next.js',
  'https://github.com/tiangolo/fastapi',
];

export default function Landing({ onAnalyze }: LandingProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const submit = () => {
    const trimmed = url.trim();
    if (!trimmed) { setError('Please enter a GitHub repository URL.'); return; }
    if (!trimmed.startsWith('http')) { setError('URL must start with http:// or https://'); return; }
    setError('');
    onAnalyze(trimmed);
  };

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') submit();
  };

  return (
    <div className="landing">
      <div className="landing-logo">
        <div className="landing-logo-icon">🔍</div>
      </div>

      <h1 className="landing-title">Codebase Visualizer</h1>
      <p className="landing-sub">
        Enter any public GitHub repository URL to instantly generate an interactive metrics dashboard.
      </p>

      <div className="landing-form">
        <div className="landing-input-wrap">
          <GitBranch size={18} style={{ color: 'var(--text-muted)', margin: 'auto 4px' }} />
          <input
            className="landing-input"
            type="url"
            placeholder="https://github.com/owner/repo"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={onKey}
            autoFocus
            id="github-url-input"
          />
          <button className="landing-btn" onClick={submit} id="analyze-btn">
            <Zap size={15} />
            Analyze
          </button>
        </div>
        {error && <div className="landing-error">{error}</div>}
      </div>

      <div className="landing-examples">
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 4 }}>Try:</span>
        {EXAMPLES.map(ex => (
          <button
            key={ex}
            className="landing-example-chip"
            onClick={() => setUrl(ex)}
          >
            {ex.replace('https://github.com/', '')}
          </button>
        ))}
      </div>
    </div>
  );
}
