import { Loader2 } from 'lucide-react';

interface LoadingProps {
  url: string;
}

export default function LoadingScreen({ url }: LoadingProps) {
  const repoName = url.replace('https://github.com/', '').split('/').slice(0, 2).join('/');

  const steps = [
    'Cloning repository...',
    'Scanning file structure...',
    'Analyzing complexity metrics...',
    'Detecting hotspots...',
    'Building visualization...',
  ];

  return (
    <div className="loading-screen">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <Loader2 size={22} style={{ color: 'var(--accent)', animation: 'spin 0.8s linear infinite' }} />
        <span className="loading-title">Analyzing {repoName}</span>
      </div>
      <span className="loading-subtitle">{url}</span>

      <div style={{ marginTop: '2rem', marginBottom: '1rem' }}>
        <div className="progress-bar-track">
          <div className="progress-bar-fill" />
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
        {steps.map((step, i) => (
          <div
            key={step}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              color: 'var(--text-secondary)',
              fontSize: '0.85rem',
              animation: `fadein 0.4s ease ${i * 0.3}s both`,
            }}
          >
            <span style={{ color: 'var(--success)', fontFamily: 'monospace' }}>›</span>
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
