import { X, MapPin, CloudRain, AlertTriangle, TrendingUp } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export default function DistrictDetailModal({ district, onClose }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const d = district;
  const pHeavy = d.p_heavy || d.pHeavy || 0;
  const pVeryHeavy = d.p_very_heavy || d.pVeryHeavy || 0;
  const pExtreme = d.p_extreme || d.pExtreme || 0;
  const pModerate = d.p_moderate || d.pModerate || 0;

  const stats = [
    { label: 'Raw NWP Forecast', value: `${d.raw} mm`, icon: CloudRain, color: 'text-slate-400' },
    { label: 'AI Corrected Forecast', value: `${d.corrected} mm`, icon: TrendingUp, color: 'text-cyan-400' },
    { label: 'P(Moderate > 7.5mm)', value: `${(pModerate * 100).toFixed(1)}%`, icon: AlertTriangle, color: 'text-blue-400' },
    { label: 'P(Heavy > 64.5mm)', value: `${(pHeavy * 100).toFixed(1)}%`, icon: AlertTriangle, color: 'text-amber-400' },
    { label: 'P(Very Heavy > 124.5mm)', value: `${(pVeryHeavy * 100).toFixed(1)}%`, icon: AlertTriangle, color: 'text-orange-400' },
    { label: 'P(Extreme > 244.5mm)', value: `${(pExtreme * 100).toFixed(1)}%`, icon: AlertTriangle, color: 'text-red-400' },
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[99999] flex items-center justify-center animate-fade-in" onClick={onClose}>
      <div className={`w-[520px] rounded-2xl shadow-2xl border overflow-hidden animate-fade-slide-up ${isDark ? 'bg-[#1e293b] border-white/10' : 'bg-white border-gray-200'}`} onClick={e => e.stopPropagation()}>
        <div className={`px-6 py-4 border-b flex items-center justify-between ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
          <div>
            <h3 className={`text-[16px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</h3>
            <p className={`text-[12px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{d.state} | {d.regime?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
          </div>
          <button onClick={onClose} className={`p-2 rounded-xl transition-colors ${isDark ? 'hover:bg-white/10 text-slate-400' : 'hover:bg-gray-100 text-gray-500'}`}>
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 space-y-3">
          {stats.map((s, i) => (
            <div key={s.label} className={`flex items-center justify-between p-3 rounded-xl transition-colors ${isDark ? 'bg-white/5 hover:bg-white/8' : 'bg-gray-50 hover:bg-gray-100'}`}>
              <div className="flex items-center gap-3">
                <s.icon className={`w-5 h-5 ${s.color}`} />
                <span className={`text-[13px] ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>{s.label}</span>
              </div>
              <span className={`text-[14px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{s.value}</span>
            </div>
          ))}
          <div className={`p-3 rounded-xl ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-3 mb-2">
              <MapPin className="w-5 h-5 text-cyan-400" />
              <span className={`text-[13px] ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>Location</span>
            </div>
            <div className={`text-[12px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Lat: {d.lat} | Lon: {d.lon}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
