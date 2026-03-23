import { useState, useEffect } from 'react';
import type { FileNode } from '../types';
import { AlertCircle, FileCode } from 'lucide-react';

interface Suggestion {
  line: number;
  message: string;
}

interface CodeViewerProps {
  file: FileNode;
  sessionPath?: string;
}

export default function CodeViewer({ file, sessionPath }: CodeViewerProps) {
  const [content, setContent] = useState<string>('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let unmounted = false;
    setLoading(true);
    setError('');

    if (!sessionPath) {
      setError('Session path is missing, cannot load file.');
      setLoading(false);
      return;
    }

    const fetchCode = async () => {
      try {
        const query = new URLSearchParams({
          session_path: sessionPath,
          path: file.path
        });
        const res = await fetch(`http://localhost:5000/api/file?${query.toString()}`);
        const data = await res.json();

        if (!unmounted) {
          if (!res.ok || data.error) {
            setError(data.error || 'Failed to load file');
          } else {
            setContent(data.content || '');
            setSuggestions(data.suggestions || []);
          }
        }
      } catch (err) {
        if (!unmounted) setError('Network error fetching file code');
      } finally {
        if (!unmounted) setLoading(false);
      }
    };

    fetchCode();

    return () => { unmounted = true; };
  }, [file.path, sessionPath]);

  const lines = content.split('\n');

  // Map suggestions to their line numbers for quick lookup
  const suggestionMap = new Map<number, Suggestion[]>();
  suggestions.forEach(s => {
    const list = suggestionMap.get(s.line) || [];
    list.push(s);
    suggestionMap.set(s.line, list);
  });

  return (
    <div className="code-viewer" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="dash-panel-header" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <FileCode size={16} /> Source Code
      </div>
      
      <div className="code-container" style={{ flex: 1, overflow: 'auto', background: 'var(--surface)', padding: '1rem', borderRadius: '8px', fontSize: '13px', fontFamily: 'monospace', lineHeight: '1.5' }}>
        {loading && <div style={{ color: 'var(--text-muted)' }}>Loading file content...</div>}
        {error && <div style={{ color: 'var(--danger)' }}>{error}</div>}
        
        {!loading && !error && (
          <div style={{ display: 'grid', gridTemplateColumns: 'min-content 1fr', gap: '12px' }}>
            {lines.map((lineText, i) => {
              const lineNum = i + 1;
              const lineSuggestions = suggestionMap.get(lineNum);
              const hasWarning = !!lineSuggestions?.length;

              return (
                <div key={i} style={{ display: 'contents' }}>
                  {/* Line Number */}
                  <div style={{ 
                    textAlign: 'right', 
                    color: hasWarning ? 'var(--warning)' : 'var(--text-muted)', 
                    userSelect: 'none',
                    paddingRight: '8px',
                    borderRight: '1px solid var(--border)'
                  }}>
                    {lineNum}
                  </div>
                  
                  {/* Line Content */}
                  <div style={{ 
                    position: 'relative',
                    whiteSpace: 'pre',
                    backgroundColor: hasWarning ? 'rgba(210,153,34,0.15)' : 'transparent',
                    borderLeft: hasWarning ? '2px solid var(--warning)' : '2px solid transparent',
                    paddingLeft: '8px'
                  }}>
                    {lineText || ' '}
                    
                    {/* Inline suggestions block */}
                    {hasWarning && (
                      <div style={{
                        marginTop: '4px',
                        marginBottom: '8px',
                        padding: '6px 10px',
                        backgroundColor: 'var(--bg)',
                        border: '1px solid var(--warning)',
                        borderRadius: '4px',
                        color: 'var(--text)',
                        fontSize: '0.85em',
                        whiteSpace: 'normal',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px'
                      }}>
                        {lineSuggestions.map((s, idx) => (
                          <div key={idx} style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
                            <AlertCircle size={14} style={{ color: 'var(--warning)', flexShrink: 0, marginTop: '2px' }} />
                            <span>{s.message}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
