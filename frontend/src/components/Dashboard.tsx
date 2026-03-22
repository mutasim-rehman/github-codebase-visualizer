import type { FileNode } from '../types';
import RadarChart from './RadarChart';
import { FileCode, Hash, Code2, Cpu, AlertTriangle } from 'lucide-react';

interface FileDashboardProps {
  file: FileNode;
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

export default function FileDashboard({ file }: FileDashboardProps) {
  const filename = file.path.split(/[/\\]/).pop() ?? file.path;

  return (
    <div className="file-dash">
      <div className="file-dash-header">
        <div className="file-dash-title">
          <FileCode size={22} style={{ color: 'var(--accent)', flexShrink: 0 }} />
          {filename}
          <span className={`risk-badge ${riskBadgeClass(file)}`}>
            {riskLabel(file)}
          </span>
        </div>
        <div className="file-dash-path">{file.path}</div>
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
    </div>
  );
}
