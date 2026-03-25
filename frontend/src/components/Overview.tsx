import type { AppData, FileNode } from '../types';
import { Code2, Layers, Globe, AlertTriangle, Copy } from 'lucide-react';

interface OverviewProps {
  data: AppData;
  onSelectFile: (f: FileNode) => void;
}

const LANG_COLORS = [
  '#3b82f6', '#a371f7', '#3fb950', '#d29922', '#f85149',
  '#58a6ff', '#e3b341', '#79c0ff', '#56d364', '#ffa657',
];

export default function Overview({ data, onSelectFile }: OverviewProps) {
  const { stats, files } = data;

  const langs = Object.entries(stats.languages || {})
    .sort((a, b) => b[1] - a[1]);

  const totalLangLoc = langs.reduce((s, [, v]) => s + v, 0) || 1;

  const hotfiles = files
    .filter(f => f.risk === 'High' || f.is_dup)
    .slice(0, 12);

  const topByLoc = [...files].sort((a, b) => b.loc - a.loc).slice(0, 8);

  return (
    <div className="overview">
      <div className="overview-hero">
        <h1 className="overview-title">Project Overview</h1>
        <p className="overview-subtitle">Select a file in the tree to drill into its metrics.</p>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label"><Layers size={13} />Total Files</div>
          <div className="stat-value">{stats.total_files.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><Code2 size={13} />Lines of Code</div>
          <div className="stat-value">{stats.total_loc.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><AlertTriangle size={13} />Hotspots</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>{stats.hotspots_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><Copy size={13} />Duplicates</div>
          <div className="stat-value" style={{ color: 'var(--duplicate)' }}>{stats.duplicates_count ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><Globe size={13} />Languages</div>
          <div className="stat-value">{Object.keys(stats.languages ?? {}).length}</div>
        </div>
      </div>

      {/* Architecture Health */}
      {data.architecture_issues && data.architecture_issues.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} style={{ color: 'var(--warning)' }} /> Architecture Health & Warnings
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {data.architecture_issues.map((issue, i) => (
              <div key={i} className={`hotspot-card`} style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', padding: '1rem', borderLeft: `4px solid ${issue.severity === 'High' ? 'var(--danger)' : 'var(--warning)'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="hotspot-name" style={{ fontSize: '1.1rem', fontWeight: 600 }}>{issue.title}</div>
                  <div className={`risk-badge ${issue.severity === 'High' ? 'High' : 'Medium'}`}>{issue.severity} Severity</div>
                </div>
                <div style={{ color: 'var(--text-secondary)' }}>{issue.description}</div>
                {issue.files && issue.files.length > 0 && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Files: {issue.files.join(', ')}</div>
                )}
                <div style={{ marginTop: '0.5rem', padding: '0.8rem', background: 'var(--bg-app)', borderRadius: '4px', fontSize: '0.9rem', color: 'var(--text-primary)', borderLeft: '3px solid var(--accent)' }}>
                  <strong>Recommendation:</strong> {issue.recommendation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Priority Action Items */}
      {hotfiles.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} style={{ color: 'var(--danger)' }} /> Priority Action Items
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {hotfiles.slice(0, 5).map(f => (
              <div key={f.path} className="hotspot-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', padding: '1rem', borderLeft: '4px solid var(--danger)', cursor: 'pointer' }} onClick={() => onSelectFile(f)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="hotspot-name" style={{ fontSize: '1rem', fontWeight: 600 }}>{f.path.split(/[/\\]/).pop()}</div>
                  <div className={`risk-badge ${f.is_dup ? 'Dup' : f.risk}`}>{f.is_dup ? 'Duplicate' : f.risk + ' Risk'}</div>
                </div>
                {f.recommendations && f.recommendations.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'var(--bg-app)', padding: '0.8rem', borderRadius: '4px' }}>
                    {f.recommendations.map((rec, i) => (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.85rem' }}>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>• {rec.issue}</div>
                        <div style={{ color: 'var(--text-secondary)', paddingLeft: '10px' }}>↳ {rec.action}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Language Bar */}
      {langs.length > 0 && (
        <div className="lang-section">
          <div className="section-title">Language Breakdown</div>
          <div className="lang-bar-wrap">
            {langs.map(([lang, loc], i) => (
              <div
                key={lang}
                className="lang-bar-seg"
                style={{
                  width: `${(loc / totalLangLoc) * 100}%`,
                  background: LANG_COLORS[i % LANG_COLORS.length],
                }}
                title={`${lang}: ${loc.toLocaleString()} LOC`}
              />
            ))}
          </div>
          <div className="lang-legend">
            {langs.slice(0, 10).map(([lang, loc], i) => (
              <div key={lang} className="lang-legend-item">
                <div className="lang-dot" style={{ background: LANG_COLORS[i % LANG_COLORS.length] }} />
                <span>{lang}</span>
                <span style={{ color: 'var(--text-muted)' }}>{((loc / totalLangLoc) * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hotspot Files */}
      {hotfiles.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <div className="section-title">⚠ High-Risk & Duplicate Files</div>
          <div className="hotspot-grid">
            {hotfiles.map(f => (
              <div
                key={f.path}
                className={`hotspot-card ${f.is_dup ? 'Dup' : f.risk}`}
                onClick={() => onSelectFile(f)}
              >
                <div className="hotspot-name">{f.path.split(/[/\\]/).pop()}</div>
                <div className="hotspot-meta">
                  <span>{f.loc} LOC</span>
                  <span>{f.lang}</span>
                  {f.is_dup && <span style={{ color: 'var(--duplicate)' }}>Duplicate</span>}
                  {!f.is_dup && <span style={{ color: f.risk === 'High' ? 'var(--danger)' : 'var(--warning)' }}>{f.risk} Risk</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Largest Files */}
      <div>
        <div className="section-title">Largest Files by LOC</div>
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          <table className="detail-table" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>File</th>
                <th>Language</th>
                <th style={{ textAlign: 'right' }}>LOC</th>
                <th style={{ textAlign: 'right' }}>Risk</th>
              </tr>
            </thead>
            <tbody>
              {topByLoc.map(f => (
                <tr
                  key={f.path}
                  style={{ cursor: 'pointer' }}
                  onClick={() => onSelectFile(f)}
                >
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {f.path}
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontFamily: 'initial' }}>{f.lang}</td>
                  <td style={{ textAlign: 'right' }}>{f.loc.toLocaleString()}</td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`risk-badge ${f.is_dup ? 'Dup' : f.risk}`}>{f.is_dup ? 'Dup' : f.risk}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
