import { useState } from 'react';
import type { AppData } from '../types';
import { MermaidDiagram } from './MermaidDiagram';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { Network, GitMerge, Code2, Layers, BarChart2, AlertTriangle } from 'lucide-react';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

interface DiagramsViewProps {
  data: AppData;
}

type Tab = 'dependency' | 'class' | 'calls' | 'renders' | 'radar';

const TABS: { id: Tab; label: string; icon: React.ReactNode; description: string }[] = [
  { id: 'dependency', label: 'Module Dependencies', icon: <Network size={15} />, description: 'Shows how files import and depend on each other.' },
  { id: 'class', label: 'Class & UML Diagram', icon: <Layers size={15} />, description: 'Static structure of classes, methods, and interfaces.' },
  { id: 'calls', label: 'Function Call Graph', icon: <GitMerge size={15} />, description: 'Internal function call relationships within the codebase.' },
  { id: 'renders', label: 'React Render Tree', icon: <Code2 size={15} />, description: 'Component render hierarchy for React/UI codebases.' },
  { id: 'radar', label: 'Hotspot Radar', icon: <BarChart2 size={15} />, description: 'Multi-axis complexity comparison of the top 5 riskiest files.' },
];

const DIAGRAM_KEY_MAP: Record<Tab, keyof AppData['diagrams'] | null> = {
  dependency: 'dependency',
  class: 'class_diagram',
  calls: 'call_graph',
  renders: 'render_tree',
  radar: null,
};

export default function DiagramsView({ data }: DiagramsViewProps) {
  const [active, setActive] = useState<Tab>('dependency');

  const activeTab = TABS.find(t => t.id === active)!;
  const diagramKey = DIAGRAM_KEY_MAP[active];
  const diagramSrc = diagramKey ? data.diagrams[diagramKey] : null;

  const radarData = {
    labels: ['LOC Scale', 'Functions', 'Nesting Depth', 'Dependencies', 'Risk Score'],
    datasets: (data.hotspot_radar?.datasets ?? []).map(ds => ({
      ...ds,
      fill: true,
      borderWidth: 2,
      pointBackgroundColor: ds.borderColor,
      pointBorderColor: 'rgba(255,255,255,0.5)',
      pointRadius: 3,
      pointHoverRadius: 5,
    })),
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 10,
        angleLines: { color: 'rgba(255,255,255,0.07)' },
        grid: { color: 'rgba(255,255,255,0.07)' },
        pointLabels: {
          color: '#8b949e',
          font: { size: 12, family: "'Inter', sans-serif" },
        },
        ticks: { display: false },
      },
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#8b949e',
          font: { size: 11 },
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 8,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(19,21,26,0.95)',
        titleColor: '#f1f3f5',
        bodyColor: '#8b949e',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          label: (ctx: any) => `${ctx.dataset.label}: ${Number(ctx.raw).toFixed(1)}/10`,
        },
      },
    },
  };

  return (
    <div className="overview animate-fade-in" style={{ gap: 0 }}>
      <div className="overview-hero">
        <h1 className="overview-title" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Network size={28} style={{ color: 'var(--accent)' }} />
          Architecture Diagrams
        </h1>
        <p className="overview-subtitle">
          Visual representations of the codebase structure, dependencies, and complexity.
        </p>
      </div>

      {/* Tab Bar */}
      <div style={{
        display: 'flex',
        gap: 4,
        marginBottom: '1.5rem',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        padding: 4,
        flexWrap: 'wrap',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              padding: '8px 16px',
              borderRadius: 7,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontFamily: 'var(--font)',
              fontWeight: active === tab.id ? 600 : 400,
              background: active === tab.id ? 'var(--accent)' : 'transparent',
              color: active === tab.id ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.15s ease',
            }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Description banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 16px',
        background: 'rgba(59,130,246,0.06)',
        border: '1px solid rgba(59,130,246,0.15)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '1.5rem',
        color: 'var(--text-secondary)',
        fontSize: '0.85rem',
      }}>
        <AlertTriangle size={14} style={{ color: 'var(--accent)', flexShrink: 0 }} />
        {activeTab.description}
      </div>

      {/* Diagram Panel */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}>
        {/* Panel header with raw source toggle */}
        <DiagramPanel
          tab={active}
          diagramSrc={diagramSrc}
          radarData={radarData}
          radarOptions={radarOptions}
          hasHotspots={(data.hotspot_radar?.datasets ?? []).length > 0}
        />
      </div>
    </div>
  );
}

interface DiagramPanelProps {
  tab: Tab;
  diagramSrc: string | null;
  radarData: object;
  radarOptions: object;
  hasHotspots: boolean;
}

function DiagramPanel({ tab, diagramSrc, radarData, radarOptions, hasHotspots }: DiagramPanelProps) {
  const [showSource, setShowSource] = useState(false);

  if (tab === 'radar') {
    return (
      <div>
        <div style={{
          padding: '12px 18px',
          borderBottom: '1px solid var(--border)',
          background: 'rgba(0,0,0,0.2)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Top-5 Hotspot Complexity Radar
          </span>
        </div>
        <div style={{ padding: '2rem', display: 'flex', justifyContent: 'center' }}>
          {hasHotspots ? (
            <div style={{ width: '100%', maxWidth: 600, height: 480 }}>
              <Radar data={radarData as any} options={radarOptions as any} />
            </div>
          ) : (
            <EmptyDiagram message="No hotspots detected in this codebase — great job! 🎉" />
          )}
        </div>
      </div>
    );
  }

  if (!diagramSrc) {
    return <EmptyDiagram message="No diagram data available." />;
  }

  const lineCount = diagramSrc.split('\n').length;

  return (
    <div>
      <div style={{
        padding: '10px 18px',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(0,0,0,0.2)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {lineCount} lines of Mermaid definition
        </span>
        <button
          onClick={() => setShowSource(s => !s)}
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            borderRadius: 6,
            padding: '4px 12px',
            fontSize: '0.78rem',
            cursor: 'pointer',
            fontFamily: 'var(--font)',
          }}
        >
          {showSource ? 'Show Diagram' : 'Show Source'}
        </button>
      </div>

      {/* Portrait diagram container — narrow column, tall vertical scroll */}
      <div style={{ padding: '1.5rem 1.5rem 2rem' }}>
        {showSource ? (
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
            color: 'var(--text-secondary)',
            overflowX: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: '70vh',
            overflowY: 'auto',
          }}>
            {diagramSrc}
          </pre>
        ) : (
          /* maxWidth keeps the graph column narrow so TD layout renders portrait */
          <div style={{ maxWidth: 900, margin: '0 auto' }}>
            <MermaidDiagram
              key={`${tab}-${diagramSrc.length}`}
              definition={diagramSrc}
              id={`mermaid-${tab}`}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyDiagram({ message }: { message: string }) {
  return (
    <div style={{
      padding: '3rem',
      textAlign: 'center',
      color: 'var(--text-muted)',
      fontSize: '0.9rem',
    }}>
      {message}
    </div>
  );
}
