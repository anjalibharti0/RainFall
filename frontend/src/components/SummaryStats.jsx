import { CloudRain, Sparkles, AlertTriangle } from 'lucide-react';
import { districtForecasts } from '../data/mockData';

export default function SummaryStats() {
  const avgRaw = districtForecasts.reduce((s, d) => s + d.raw, 0) / districtForecasts.length;
  const avgCorrected = districtForecasts.reduce((s, d) => s + d.corrected, 0) / districtForecasts.length;
  const avgHeavy = districtForecasts.reduce((s, d) => s + d.pHeavy, 0) / districtForecasts.length;
  const improvement = ((avgCorrected - avgRaw) / avgRaw * 100).toFixed(0);

  const stats = [
    {
      label: 'Raw NWP Rainfall',
      value: `${avgRaw.toFixed(0)}`,
      unit: 'mm',
      sub: '(for selected area)',
      icon: CloudRain,
      iconBg: 'bg-blue-50',
      iconColor: 'text-blue-500',
      valueColor: 'text-gray-900',
    },
    {
      label: 'AI Corrected Rainfall',
      value: `${avgCorrected.toFixed(0)}`,
      unit: 'mm',
      sub: '(for selected area)',
      badge: `(+${Math.abs(improvement)}%)`,
      badgeColor: 'text-emerald-600',
      icon: Sparkles,
      iconBg: 'bg-indigo-50',
      iconColor: 'text-indigo-500',
      valueColor: 'text-gray-900',
    },
    {
      label: 'Heavy Rain Probability',
      value: `${(avgHeavy * 100).toFixed(0)}`,
      unit: '%',
      sub: '(> 64.5 mm)',
      icon: AlertTriangle,
      iconBg: 'bg-rose-50',
      iconColor: 'text-rose-500',
      valueColor: 'text-rose-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {stats.map((s) => (
        <div key={s.label} className="dashboard-card p-5 flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${s.iconBg}`}>
            <s.icon className={`w-5 h-5 ${s.iconColor}`} />
          </div>
          <div>
            <div className="text-[12px] font-medium text-gray-400">{s.label}</div>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className={`text-[28px] font-extrabold tracking-[-0.03em] ${s.valueColor}`}>
                {s.value}
              </span>
              <span className="text-[14px] font-medium text-gray-400">{s.unit}</span>
              {s.badge && (
                <span className={`text-[13px] font-bold ${s.badgeColor}`}>{s.badge}</span>
              )}
            </div>
            <div className="text-[11px] text-gray-400 mt-0.5">{s.sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
