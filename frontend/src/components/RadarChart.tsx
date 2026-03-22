import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

interface RadarChartProps {
  data: number[];
  risk: string;
  isDup: boolean;
}

export default function RadarChart({ data, risk, isDup }: RadarChartProps) {
  const rgb = isDup
    ? '227,179,65'
    : risk === 'High'
      ? '248,81,73'
      : risk === 'Medium'
        ? '210,153,34'
        : '63,185,80';

  const chartData = {
    labels: ['LOC Scale', 'Functions', 'Nesting Depth', 'Dependencies', 'Risk Score'],
    datasets: [{
      label: 'Profile',
      data,
      backgroundColor: `rgba(${rgb}, 0.18)`,
      borderColor: `rgb(${rgb})`,
      borderWidth: 2,
      pointBackgroundColor: `rgb(${rgb})`,
      pointBorderColor: 'rgba(255,255,255,0.6)',
      pointRadius: 4,
      pointHoverRadius: 6,
    }],
  };

  const options = {
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
          font: { size: 11, family: "'Inter', sans-serif" },
        },
        ticks: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(19,21,26,0.95)',
        titleColor: '#f1f3f5',
        bodyColor: '#8b949e',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 10,
        displayColors: false,
        callbacks: {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          label: (ctx: any) => `Score: ${Number(ctx.raw).toFixed(1)} / 10`,
        },
      },
    },
  };

  return <Radar data={chartData} options={options} />;
}
