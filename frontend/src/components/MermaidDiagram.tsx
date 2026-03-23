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
  // useMaxWidth: false lets us control portrait layout via CSS
  flowchart: { curve: 'basis', useMaxWidth: false },
  securityLevel: 'loose',
});

interface MermaidDiagramProps {
  definition: string;
  id: string;
}

/** Force the mermaid SVG to be portrait: full-width, tall, scroll-y only */
function portraitSvg(rawSvg: string): string {
  // Remove any fixed width/height on <svg ...> and let CSS drive it
  return rawSvg
    .replace(/<svg([^>]*?)width="[^"]*"([^>]*?)>/g, '<svg$1$2>')
    .replace(/<svg([^>]*?)height="[^"]*"([^>]*?)>/g, '<svg$1$2>')
    .replace(/<svg([^>]*)>/g, '<svg$1 style="width:100%;height:auto;display:block;">');
}

export function MermaidDiagram({ definition, id }: MermaidDiagramProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [svg, setSvg] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setSvg('');

    // Cap enormously large graphs for performance
    const lines = definition.split('\n');
    const nodeLines = lines.filter(l => /^\s+(F\d+)\[/.test(l));
    const edgeLines = lines.filter(l => /-->/.test(l));

    let def = definition;
    if (nodeLines.length > 100 || edgeLines.length > 180) {
      const capped = [lines[0]];
      let nodeCnt = 0;
      let edgeCnt = 0;
      for (const line of lines.slice(1)) {
        if (/^\s+(F\d+)\[/.test(line)) {
          if (nodeCnt < 100) { capped.push(line); nodeCnt++; }
        } else if (/-->/.test(line)) {
          if (edgeCnt < 180) { capped.push(line); edgeCnt++; }
        } else {
          capped.push(line);
        }
      }
      capped.push('    truncNote["⚠ Graph truncated — showing first 100 nodes"]');
      def = capped.join('\n');
    }

    mermaid.render(id, def)
      .then(({ svg: rendered }) => {
        if (!cancelled) setSvg(portraitSvg(rendered));
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
        <span style={{ display: 'inline-block', marginRight: 10, fontSize: '1.2rem', animation: 'spin 1s linear infinite' }}>⟳</span>
        Rendering diagram…
      </div>
    );
  }

  return (
    <div
      ref={wrapRef}
      style={{
        width: '100%',
        overflowY: 'auto',   // scroll vertically (portrait)
        overflowX: 'hidden', // no horizontal scroll
        maxHeight: '75vh',
        padding: '0.5rem 0',
      }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
