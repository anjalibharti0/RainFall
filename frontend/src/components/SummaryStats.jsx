import { CloudRain, Sparkles, AlertTriangle } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function SummaryStats({ districts = [] }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (districts.length === 0) {
    return (
      <div className="flex flex-col gap-4 h-full">
        {[1,2,3].map(i => (
          <div key={i} className="glass-card p-5 flex items-center gap-4 flex-1 animate-pulse">
            <div className="w-12 h-12 rounded-xl bg-white/5" />
            <div className="space-y-2"><div className="h-3 w-24 bg-white/5 rounded" /><div className="h-6 w-16 bg-white/5 rounded" /></div>
          </div>
        ))}
      </div>
    );
  }

  const avgRaw = districts.reduce((s, d) => s + (d.raw || 0), 0) / districts.length;
  const avgCorrected = districts.reduce((s, d) => s + (d.corrected || 0), 0) / districts.length;
  const avgHeavy = districts.reduce((s, d) => s + (d.p_heavy || d.pHeavy || 0), 0) / districts.length;
  const improvement = avgRaw > 0 ? ((avgCorrected - avgRaw) / avgRaw * 100).toFixed(0) : 0;

  const stats = [
    { label: 'Raw NWP Rainfall', value: avgRaw.toFixed(0), unit: 'mm', sub: `Across ${districts.length} districts`, icon: CloudRain, iconBg: 'bg-cyan-500/20', iconColor: 'text-cyan-400' },
    { label: 'AI Corrected Rainfall', value: avgCorrected.toFixed(0), unit: 'mm', sub: `Across ${districts.length} districts`, badge: `(+${Math.abs(improvement)}%)`, badgeColor: 'text-emerald-400', icon: Sparkles, iconBg: 'bg-purple-500/20', iconColor: 'text-purple-400' },
    { label: 'Heavy Rain Probability', value: (avgHeavy * 100).toFixed(0), unit: '%', sub: '(> 64.5 mm)', icon: AlertTriangle, iconBg: 'bg-rose-500/20', iconColor: 'text-rose-400' },
  ];

  return (
    <div className="flex flex-col gap-4 h-full">
      {stats.map((s) => (
        <div key={s.label} className="glass-card glass-card-hover p-5 flex items-center gap-4 flex-1">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${s.iconBg} flex-shrink-0`}>
            <s.icon className={`w-5 h-5 ${s.iconColor}`} />
          </div>
          <div>
            <div className={`text-[12px] font-medium ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{s.label}</div>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className={`text-[28px] font-extrabold tracking-[-0.03em] ${isDark ? 'text-white' : 'text-gray-900'}`}>{s.value}</span>
              <span className={`text-[14px] font-medium ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{s.unit}</span>
              {s.badge && <span className={`text-[13px] font-bold ${s.badgeColor}`}>{s.badge}</span>}
            </div>
            <div className={`text-[11px] mt-0.5 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>{s.sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
