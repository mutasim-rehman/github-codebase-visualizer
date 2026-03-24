import { useState } from 'react';
import type { FileNode } from '../types';
import RadarChart from './RadarChart';
import CodeViewer from './CodeViewer';
import { FileCode, Hash, Code2, Cpu, AlertTriangle } from 'lucide-react';

interface FileDashboardProps {
  file: FileNode;
  sessionPath?: string;
}

function riskBadgeClass(file: FileNode) {
  if (file.is_dup) return 'Dup';
  return file.risk;
}

function riskLabel(file: FileNode) {
  if (file.is_dup) return '⚠ Duplicate Code';
  if (file.is_gen) return '⚙ Generated';
  return `${file.risk} Risk`;
}

export default function FileDashboard({ file, sessionPath }: FileDashboardProps) {
  const filename = file.path.split(/[/\\]/).pop() ?? file.path;
  const [viewMode, setViewMode] = useState<'metrics' | 'code'>('metrics');

  return (
    <div className="file-dash" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="file-dash-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="file-dash-title">
            <FileCode size={22} style={{ color: 'var(--accent)', flexShrink: 0 }} />
            {filename}
            <span className={`risk-badge ${riskBadgeClass(file)}`}>
              {riskLabel(file)}
            </span>
          </div>
          <div className="file-dash-path">{file.path}</div>
        </div>
        
        <div style={{ display: 'flex', gap: '8px', background: 'var(--surface)', padding: '4px', borderRadius: '6px' }}>
          <button 
            style={{ 
              padding: '6px 12px', 
              borderRadius: '4px',
              border: 'none',
              background: viewMode === 'metrics' ? 'var(--accent)' : 'transparent',
              color: viewMode === 'metrics' ? '#fff' : 'var(--text-muted)',
              cursor: 'pointer'
            }}
            onClick={() => setViewMode('metrics')}
          >
            Metrics
          </button>
          <button 
             style={{ 
              padding: '6px 12px', 
              borderRadius: '4px',
              border: 'none',
              background: viewMode === 'code' ? 'var(--accent)' : 'transparent',
              color: viewMode === 'code' ? '#fff' : 'var(--text-muted)',
              cursor: 'pointer'
            }}
            onClick={() => setViewMode('code')}
          >
            View Code
          </button>
        </div>
      </div>

      <div className="metrics-row">
        <div className="metric-tile">
          <div className="metric-tile-label"><Code2 size={12} /> Lines of Code</div>
          <div className="metric-tile-value">{file.loc.toLocaleString()}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-tile-label"><Hash size={12} /> Language</div>
          <div className="metric-tile-value" style={{ fontSize: '1.2rem' }}>{file.lang}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-tile-label"><Cpu size={12} /> Functions</div>
          <div className="metric-tile-value">{file.functions.length}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-tile-label"><AlertTriangle size={12} /> Risk Score</div>
          <div
            className="metric-tile-value"
            style={{
              color: file.is_dup
                ? 'var(--duplicate)'
                : file.risk === 'High'
                  ? 'var(--danger)'
                  : file.risk === 'Medium'
                    ? 'var(--warning)'
                    : 'var(--success)'
            }}
          >
            {Number(file.score).toFixed(1)}
          </div>
        </div>
      </div>
      
      {file.reasons && file.reasons.length > 0 && (
        <div style={{ margin: '0 1.5rem 1rem', padding: '0.75rem', background: 'var(--surface)', borderLeft: '3px solid var(--warning)', borderRadius: '4px', fontSize: '0.9rem' }}>
          <div style={{ fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
             <AlertTriangle size={14} style={{ color: 'var(--warning)' }} /> Risk Factors
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)' }}>
            {file.reasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      {viewMode === 'code' ? (
        <div style={{ flex: 1, minHeight: 0, marginTop: '1rem' }}>
          <CodeViewer file={file} sessionPath={sessionPath} />
        </div>
      ) : (
      <>
        <div className="dash-grid">
        {/* Radar Chart */}
        <div className="dash-panel">
          <div className="dash-panel-header">Complexity Profile</div>
          <div className="chart-wrap">
            <RadarChart data={file.radar} risk={file.risk} isDup={file.is_dup} />
          </div>
        </div>

        {/* Anatomy Panel */}
        <div className="dash-panel">
          <div className="dash-panel-header">Module Anatomy</div>
          <div className="dash-panel-body">
            {/* Classes */}
            <div className="detail-section">
              <div className="detail-section-title">Classes & Components</div>
              {file.classes.length > 0 ? (
                <table className="detail-table">
                  <thead><tr><th>Name</th><th>Methods</th></tr></thead>
                  <tbody>
                    {file.classes.map((c, i) => (
                      <tr key={i}>
                        <td>{c.name}</td>
                        <td style={{ color: 'var(--text-secondary)', fontFamily: 'initial' }}>{c.methods}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-detail">No classes detected.</div>
              )}
            </div>

            {/* Functions */}
            <div className="detail-section">
              <div className="detail-section-title">Functions</div>
              {file.functions.length > 0 ? (
                <table className="detail-table">
                  <thead><tr><th>Name</th><th style={{ textAlign: 'right' }}>LOC</th></tr></thead>
                  <tbody>
                    {file.functions.map((fn, i) => (
                      <tr key={i}>
                        <td>{fn.name}</td>
                        <td style={{ textAlign: 'right', color: 'var(--text-secondary)', fontFamily: 'initial' }}>{fn.loc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-detail">No functions detected.</div>
              )}
            </div>

            {/* Imports */}
            <div className="detail-section">
              <div className="detail-section-title">Dependencies / Imports</div>
              {file.imports.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                  {file.imports.map((imp, i) => (
                    <span key={i} className="import-pill">{imp}</span>
                  ))}
                  {file.imports.length === 20 && (
                    <span className="import-pill" style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>+more…</span>
                  )}
                </div>
              ) : (
                <div className="empty-detail">No imports detected.</div>
              )}
            </div>
          </div>
        </div>
      </div>
      </>
      )}
    </div>
  );
}
