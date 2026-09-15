import { CloudRain } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function HeavyRainProbability({ districts = [] }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (districts.length === 0) {
    return (
      <div className="glass-card overflow-hidden h-full flex flex-col">
        <div className={`px-5 py-4 border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
          <h3 className={`text-[15px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Heavy Rainfall Probability</h3>
        </div>
        <div className="p-5 flex-1 flex items-center justify-center">
          <div className="space-y-3 w-full">
            {[1,2,3].map(i => <div key={i} className="h-16 skeleton" />)}
          </div>
        </div>
      </div>
    );
  }

  const avgHeavy = districts.reduce((s, d) => s + (d.p_heavy || d.pHeavy || 0), 0) / districts.length;
  const avgVeryHeavy = districts.reduce((s, d) => s + (d.p_very_heavy || d.pVeryHeavy || 0), 0) / districts.length;
  const avgExtreme = districts.reduce((s, d) => s + (d.p_extreme || d.pExtreme || 0), 0) / districts.length;

  const categories = [
    { label: '> 64.5 mm (Heavy)', value: (avgHeavy * 100).toFixed(0), bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/20', glow: 'hover:shadow-emerald-500/10' },
    { label: '> 115.6 mm (Very Heavy)', value: (avgVeryHeavy * 100).toFixed(0), bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/20', glow: 'hover:shadow-amber-500/10' },
    { label: '> 204.5 mm (Ext. Heavy)', value: (avgExtreme * 100).toFixed(0), bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/20', glow: 'hover:shadow-purple-500/10' },
  ];

  return (
    <div className="glass-card overflow-hidden h-full flex flex-col">
      <div className={`px-5 py-4 border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
        <h3 className={`text-[15px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Heavy Rainfall Probability <span className={`font-normal text-[12px] ${isDark ? 'text-slate-400' : 'text-gray-400'}`}>(All Districts Avg)</span></h3>
      </div>
      <div className="p-5 flex flex-col gap-4 flex-1">
        {categories.map((c) => (
          <div key={c.label} className={`border ${c.border} rounded-xl p-4 flex items-center gap-4 interactive-hover cursor-default shadow-lg ${c.glow}`}>
            <div className={`w-12 h-12 rounded-xl ${c.bg} flex items-center justify-center flex-shrink-0`}>
              <CloudRain className={`w-6 h-6 ${c.text}`} />
            </div>
            <div>
              <div className={`text-[12px] font-medium ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{c.label}</div>
              <div className={`text-[28px] font-extrabold tracking-[-0.03em] ${c.text}`}>{c.value}%</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
