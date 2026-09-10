import { useState } from 'react';
import { Search } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export default function DistrictTable({ districts = [], onDistrictClick }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [search, setSearch] = useState('');

  const filtered = districts
    .filter(d => !search || d.name?.toLowerCase().includes(search.toLowerCase()) || d.state?.toLowerCase().includes(search.toLowerCase()))
    .slice(0, 20);

  const regimeColors = {
    active_monsoon: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400' },
    break_monsoon: { bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400' },
    depression: { bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400' },
    orographic: { bg: 'bg-purple-500/15', text: 'text-purple-400', dot: 'bg-purple-400' },
    coastal: { bg: 'bg-cyan-500/15', text: 'text-cyan-400', dot: 'bg-cyan-400' },
    western_disturbance: { bg: 'bg-indigo-500/15', text: 'text-indigo-400', dot: 'bg-indigo-400' },
  };

  return (
    <div className="glass-card overflow-hidden h-full flex flex-col">
      <div className={`px-5 py-4 border-b flex items-center justify-between ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
        <h3 className={`text-[15px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>District Forecast ({districts.length})</h3>
        <div className="relative">
          <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${isDark ? 'text-slate-500' : 'text-gray-400'}`} />
          <input
            type="text"
            placeholder="Search district..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`pl-9 pr-3 py-2 rounded-lg text-[12px] w-[180px] outline-none border ${
              isDark ? 'bg-white/5 border-white/10 focus:border-cyan-500/50 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-200 focus:border-cyan-500 text-gray-900 placeholder-gray-400'
            }`}
          />
        </div>
      </div>
      <div className="overflow-auto flex-1">
        <table className="w-full">
          <thead className={`sticky top-0 ${isDark ? 'bg-[#0f172a]' : 'bg-white'}`}>
            <tr className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
              <th className={`text-left text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>District</th>
              <th className={`text-right text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Raw (mm)</th>
              <th className={`text-right text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>AI Corrected (mm)</th>
              <th className={`text-right text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>P(Heavy)</th>
              <th className={`text-center text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Regime</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d, i) => {
              const rc = regimeColors[d.regime] || regimeColors.active_monsoon;
              const pHeavy = d.p_heavy || d.pHeavy || 0;
              return (
                <tr
                  key={d.district_id || d.id || i}
                  className={`border-b cursor-pointer transition-colors ${isDark ? 'border-white/5 hover:bg-white/[0.02]' : 'border-gray-50 hover:bg-cyan-50/50'}`}
                  onClick={() => onDistrictClick?.(d)}
                >
                  <td className={`px-5 py-3 text-[13px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</td>
                  <td className={`px-5 py-3 text-[13px] text-right ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{d.raw}</td>
                  <td className={`px-5 py-3 text-[13px] font-semibold text-right ${isDark ? 'text-cyan-400' : 'text-cyan-600'}`}>{d.corrected}</td>
                  <td className={`px-5 py-3 text-[13px] font-semibold text-right ${isDark ? 'text-white' : 'text-gray-900'}`}>{(pHeavy * 100).toFixed(0)}%</td>
                  <td className="px-5 py-3 text-center">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${rc.bg} ${rc.text}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${rc.dot}`} />
                      {d.regime?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
