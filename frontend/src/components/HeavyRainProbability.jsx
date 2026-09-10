import { CloudRain } from 'lucide-react';
import { districtForecasts } from '../data/mockData';

export default function HeavyRainProbability() {
  const avgHeavy = districtForecasts.reduce((s, d) => s + d.pHeavy, 0) / districtForecasts.length;
  const avgVeryHeavy = districtForecasts.reduce((s, d) => s + d.pVeryHeavy, 0) / districtForecasts.length;
  const avgExtreme = districtForecasts.reduce((s, d) => s + d.pExtreme, 0) / districtForecasts.length;

  const categories = [
    {
      label: '> 64.5 mm (Heavy)',
      value: (avgHeavy * 100).toFixed(0),
      color: 'text-amber-700',
      bg: 'bg-amber-50',
      border: 'border-amber-100',
      iconBg: 'bg-amber-100',
    },
    {
      label: '> 115.6 mm (Very Heavy)',
      value: (avgVeryHeavy * 100).toFixed(0),
      color: 'text-rose-600',
      bg: 'bg-rose-50',
      border: 'border-rose-100',
      iconBg: 'bg-rose-100',
    },
    {
      label: '> 204.5 mm (Ext. Heavy)',
      value: (avgExtreme * 100).toFixed(0),
      color: 'text-purple-700',
      bg: 'bg-purple-50',
      border: 'border-purple-100',
      iconBg: 'bg-purple-100',
    },
  ];

  return (
    <div className="dashboard-card p-0 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">
          Heavy Rainfall Probability <span className="text-gray-400 font-normal text-[12px]">(Selected Area)</span>
        </h3>
      </div>
      <div className="p-5 grid grid-cols-3 gap-4">
        {categories.map((c) => (
          <div key={c.label} className={`${c.bg} ${c.border} border rounded-xl p-4 text-center`}>
            <div className={`w-10 h-10 rounded-lg ${c.iconBg} flex items-center justify-center mx-auto mb-3`}>
              <CloudRain className={`w-5 h-5 ${c.color}`} />
            </div>
            <div className="text-[12px] font-medium text-gray-500 mb-1">{c.label}</div>
            <div className={`text-[28px] font-extrabold tracking-[-0.03em] ${c.color}`}>
              {c.value}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
