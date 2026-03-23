import { useState, type KeyboardEvent } from 'react';
import { GitBranch, FolderOpen, Zap } from 'lucide-react';

export type AnalyzeMode = 'github' | 'local';

interface LandingProps {
  onAnalyze: (input: string, mode: AnalyzeMode) => void;
}

const GITHUB_EXAMPLES = [
  'https://github.com/facebook/react',
  'https://github.com/vercel/next.js',
  'https://github.com/tiangolo/fastapi',
];

const LOCAL_EXAMPLES = [
  'C:\\Users\\username\\my-project',
  'D:\\projects\\api-service',
  '/home/user/projects/my-app',
];

export default function Landing({ onAnalyze }: LandingProps) {
  const [mode, setMode] = useState<AnalyzeMode>('github');
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  const examples = mode === 'github' ? GITHUB_EXAMPLES : LOCAL_EXAMPLES;

  const submit = () => {
    const trimmed = input.trim();
    if (!trimmed) {
      setError(mode === 'github' ? 'Please enter a GitHub repository URL.' : 'Please enter a local directory path.');
      return;
    }
    if (mode === 'github' && !trimmed.startsWith('http')) {
      setError('URL must start with http:// or https://');
      return;
    }
    setError('');
    onAnalyze(trimmed, mode);
  };

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') submit();
  };

  const switchMode = (m: AnalyzeMode) => {
    setMode(m);
    setInput('');
    setError('');
  };

  return (
    <div className="landing">
      <div className="landing-logo">
        <div className="landing-logo-icon">🔍</div>
      </div>

      <h1 className="landing-title">Codebase Visualizer</h1>
      <p className="landing-sub">
        Analyze any GitHub repository or local directory to generate an interactive metrics dashboard.
      </p>

      {/* Mode toggle */}
      <div style={{
        display: 'flex',
        gap: 4,
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        padding: 4,
        marginBottom: '1.25rem',
      }}>
        <button
          id="mode-github"
          onClick={() => switchMode('github')}
          style={{
            display: 'flex', alignItems: 'center', gap: 7,
            padding: '8px 22px', borderRadius: 6, border: 'none', cursor: 'pointer',
            fontFamily: 'var(--font)', fontSize: '0.87rem', fontWeight: mode === 'github' ? 600 : 400,
            background: mode === 'github' ? 'var(--accent)' : 'transparent',
            color: mode === 'github' ? '#fff' : 'var(--text-secondary)',
            transition: 'all 0.15s',
          }}
        >
          <GitBranch size={14} />
          GitHub URL
        </button>
        <button
          id="mode-local"
          onClick={() => switchMode('local')}
          style={{
            display: 'flex', alignItems: 'center', gap: 7,
            padding: '8px 22px', borderRadius: 6, border: 'none', cursor: 'pointer',
            fontFamily: 'var(--font)', fontSize: '0.87rem', fontWeight: mode === 'local' ? 600 : 400,
            background: mode === 'local' ? 'var(--accent)' : 'transparent',
            color: mode === 'local' ? '#fff' : 'var(--text-secondary)',
            transition: 'all 0.15s',
          }}
        >
          <FolderOpen size={14} />
          Local Path
        </button>
      </div>

      <div className="landing-form">
        <div className="landing-input-wrap">
          {mode === 'github'
            ? <GitBranch size={18} style={{ color: 'var(--text-muted)', margin: 'auto 4px' }} />
            : <FolderOpen size={18} style={{ color: 'var(--text-muted)', margin: 'auto 4px' }} />
          }
          <input
            className="landing-input"
            type="text"
            placeholder={mode === 'github' ? 'https://github.com/owner/repo' : 'C:\\path\\to\\your\\project'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKey}
            autoFocus
            id="analyze-input"
          />
          <button className="landing-btn" onClick={submit} id="analyze-btn">
            <Zap size={15} />
            Analyze
          </button>
        </div>
        {error && <div className="landing-error">{error}</div>}

        {/* Local path helper note */}
        {mode === 'local' && (
          <div style={{
            marginTop: 10,
            padding: '8px 14px',
            background: 'rgba(59,130,246,0.07)',
            border: '1px solid rgba(59,130,246,0.18)',
            borderRadius: 7,
            fontSize: '0.79rem',
            color: 'var(--text-muted)',
            textAlign: 'left',
          }}>
            💡 The server must have read access to this path. On Windows use full paths like <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>C:\Users\you\project</code>
          </div>
        )}
      </div>

      <div className="landing-examples">
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 4 }}>
          {mode === 'github' ? 'Try:' : 'Example paths:'}
        </span>
        {examples.map(ex => (
          <button
            key={ex}
            className="landing-example-chip"
            onClick={() => setInput(ex)}
          >
            {mode === 'github' ? ex.replace('https://github.com/', '') : ex}
          </button>
        ))}
      </div>
    </div>
  );
}
