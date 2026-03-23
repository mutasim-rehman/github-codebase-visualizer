import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    background: '#13151a',
    primaryColor: '#1e2330',
    primaryTextColor: '#c9d1d9',
    primaryBorderColor: '#30363d',
    lineColor: '#58a6ff',
    secondaryColor: '#1e2330',
    tertiaryColor: '#0d1117',
    edgeLabelBackground: '#13151a',
    clusterBkg: '#1e2330',
    titleColor: '#e6edf3',
    attributeBackgroundColorOdd: '#1e2330',
    attributeBackgroundColorEven: '#161b22',
  },
  flowchart: { curve: 'basis', useMaxWidth: true },
  securityLevel: 'loose',
});

interface MermaidDiagramProps {
  definition: string;
  id: string;
}

export function MermaidDiagram({ definition, id }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [svg, setSvg] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setSvg('');

    // Limit very large graphs to avoid browser freeze
    const lines = definition.split('\n');
    const nodeLines = lines.filter(l => /^\s+(F\d+)\[/.test(l));
    const edgeLines = lines.filter(l => /-->/.test(l));

    let def = definition;
    // Cap at 120 nodes and 200 edges for performance
    if (nodeLines.length > 120 || edgeLines.length > 200) {
      const capped = [lines[0]]; // keep header like "graph TD"
      let nodeCnt = 0;
      let edgeCnt = 0;
      for (const line of lines.slice(1)) {
        if (/^\s+(F\d+)\[/.test(line)) {
          if (nodeCnt < 120) { capped.push(line); nodeCnt++; }
        } else if (/-->/.test(line)) {
          if (edgeCnt < 200) { capped.push(line); edgeCnt++; }
        } else {
          capped.push(line);
        }
      }
      capped.push('    note["⚠ Graph truncated for performance"]');
      def = capped.join('\n');
    }

    mermaid.render(id, def)
      .then(({ svg: rendered }) => {
        if (!cancelled) setSvg(rendered);
      })
      .catch(err => {
        if (!cancelled) setError(String(err));
      });

    return () => { cancelled = true; };
  }, [definition, id]);

  if (error) {
    return (
      <div style={{
        padding: '1.5rem',
        background: 'rgba(248,81,73,0.08)',
        border: '1px solid rgba(248,81,73,0.3)',
        borderRadius: 8,
        color: 'var(--text-secondary)',
        fontSize: '0.82rem',
        fontFamily: 'var(--font-mono)',
      }}>
        <div style={{ color: 'var(--danger)', marginBottom: 8, fontWeight: 600 }}>⚠ Diagram render error</div>
        {error}
      </div>
    );
  }

  if (!svg) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--text-muted)' }}>
        <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block', marginRight: 10, fontSize: '1.2rem' }}>⟳</span>
        Rendering diagram…
      </div>
    );
  }

  return (
    <div
      ref={ref}
      style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: 600 }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
