import { Home, Cloud, CloudRain, AlertTriangle, MapPin, BarChart3, Settings } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export default function Sidebar({ activeView, setActiveView }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'regime', label: 'Regime Analysis', icon: Cloud },
    { id: 'rainfall', label: 'Rainfall Forecast', icon: CloudRain },
    { id: 'probability', label: 'Heavy Rain Probability', icon: AlertTriangle },
    { id: 'district', label: 'District Forecast', icon: MapPin },
    { id: 'verification', label: 'Verification Report', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className={`w-[220px] flex-shrink-0 transition-colors ${
      isDark ? 'bg-[#0f172a]/80 border-white/5' : 'bg-white/90 border-gray-200'
    } border-r`}>
      <nav className="flex-1 py-4 px-3">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all mb-1 ${
              activeView === item.id
                ? isDark
                  ? 'bg-white/10 text-white font-semibold border border-white/10'
                  : 'bg-gray-100 text-gray-900 font-semibold border border-gray-200'
                : isDark
                  ? 'text-slate-400 hover:bg-white/5 hover:text-white border border-transparent'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900 border border-transparent'
            }`}
          >
            <item.icon className={`w-[18px] h-[18px] ${
              activeView === item.id
                ? isDark ? 'text-white' : 'text-gray-900'
                : isDark ? 'text-slate-500' : 'text-gray-400'
            }`} />
            <span className="text-[13px]">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className={`p-4 border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
        <div className={`text-[11px] leading-relaxed ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>
          Smarter data.<br/>Better models.<br/>Safer communities.
        </div>
      </div>
    </aside>
  );
}
