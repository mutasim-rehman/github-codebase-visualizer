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
    fontSize: '14px',
  },
  flowchart: { curve: 'basis', useMaxWidth: false },
  securityLevel: 'loose',
});

interface MermaidDiagramProps {
  definition: string;
  id: string;
}

/**
 * Makes the SVG fill the container width and scale proportionally tall.
 *
 * Strategy:
 * 1. Parse the viewBox to get the natural aspect ratio (h / w).
 * 2. Remove the SVG's hardcoded width/height attributes.
 * 3. Inject width="100%" + a computed pixel height derived from the
 *    container width × aspect ratio (clamped to at least 480px).
 *
 * Result: diagram stretches to full column width and grows downward —
 * no horizontal scrolling needed.
 */
function scaleToPortrait(rawSvg: string, containerWidth: number): string {
  // Pull the full viewBox string, e.g. "0 0 2140.5 983.25"
  const vbMatch = rawSvg.match(/viewBox="([\d.\s-]+)"/);
  let computedHeight = 520; // sensible fallback

  if (vbMatch) {
    const parts = vbMatch[1].trim().split(/\s+/);
    if (parts.length === 4) {
      const vbW = parseFloat(parts[2]);
      const vbH = parseFloat(parts[3]);
      if (vbW > 0 && vbH > 0) {
        const ratio = vbH / vbW;
        // Scale the height proportionally; enforce a minimum for readability
        computedHeight = Math.max(480, Math.round(containerWidth * ratio));
      }
    }
  }

  // Strip the original width / height attributes that lock SVG to fixed px
  let svg = rawSvg
    .replace(/(<svg[^>]*?)\s+width="[^"]*"/, '$1')
    .replace(/(<svg[^>]*?)\s+height="[^"]*"/, '$1');

  // Inject responsive dimensions
  svg = svg.replace(
    '<svg',
    `<svg width="100%" height="${computedHeight}px" style="display:block;"`
  );

  return svg;
}

export function MermaidDiagram({ definition, id }: MermaidDiagramProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [svg, setSvg] = useState<string>('');
  const [truncated, setTruncated] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setSvg('');
    setTruncated(false);

    // Cap enormous graphs before handing to Mermaid
    const lines = definition.split('\n');
    const nodeLines = lines.filter(l => /^\s+\w+(\[|{|\()/.test(l) && !/subgraph|end|%%/.test(l));
    const edgeLines  = lines.filter(l => /-->/.test(l));
    const MAX_NODES = 90;
    const MAX_EDGES = 130;

    let def = definition;
    let wasTruncated = false;

    if (nodeLines.length > MAX_NODES || edgeLines.length > MAX_EDGES) {
      wasTruncated = true;
      const capped = [lines[0]];
      let nodeCnt = 0, edgeCnt = 0;
      for (const line of lines.slice(1)) {
        const isNode = /^\s+\w+(\[|{|\()/.test(line) && !/subgraph|end|%%/.test(line);
        const isEdge = /-->/.test(line);
        if (isNode) { if (nodeCnt < MAX_NODES) { capped.push(line); nodeCnt++; } }
        else if (isEdge) { if (edgeCnt < MAX_EDGES) { capped.push(line); edgeCnt++; } }
        else { capped.push(line); }
      }
      def = capped.join('\n');
    }

    mermaid.render(id, def)
      .then(({ svg: rendered }) => {
        if (cancelled) return;
        // Get current container width for aspect-ratio scaling
        const w = wrapRef.current?.clientWidth ?? 860;
        setSvg(scaleToPortrait(rendered, w));
        setTruncated(wasTruncated);
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
        <div style={{ marginBottom: 8 }}>{error}</div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          Switch to "Show Source" to inspect the raw Mermaid definition.
        </div>
      </div>
    );
  }

  if (!svg) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        height: 260, gap: 12, color: 'var(--text-muted)',
      }}>
        <div style={{
          width: 28, height: 28,
          border: '2px solid var(--border)',
          borderTopColor: 'var(--accent)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        Rendering diagram…
      </div>
    );
  }

  return (
    <div>
      {truncated && (
        <div style={{
          marginBottom: 10,
          padding: '6px 14px',
          background: 'rgba(210,153,34,0.1)',
          border: '1px solid rgba(210,153,34,0.3)',
          borderRadius: 6,
          fontSize: '0.78rem',
          color: 'var(--warning, #d29922)',
        }}>
          ⚠ Large diagram — only the first 90 nodes / 130 edges shown. Use "Show Source" for the full definition.
        </div>
      )}

      {/*
        overflow-y: auto  → vertical scroll when diagram is taller than viewport
        overflow-x: hidden → NO horizontal scroll — SVG fills full width
      */}
      <div
        ref={wrapRef}
        style={{
          width: '100%',
          overflowY: 'auto',
          overflowX: 'hidden',
          maxHeight: '82vh',
        }}
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
}
