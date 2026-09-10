import { REGIMES } from '../../data/mockData';
import { Map, BarChart3, CheckCircle, Layers } from 'lucide-react';

export default function Sidebar({ activeView, setActiveView, regime, districts }) {
  const regimeType = regime?.type || 'active_monsoon';
  const regimeInfo = REGIMES[regimeType] || REGIMES.active_monsoon;
  const confidence = regime?.confidence || 0.87;
  const heavyCount = districts.filter(d => (d.p_heavy || 0) > 0.5).length;
  const maxRain = districts.length > 0 ? Math.max(...districts.map(d => d.corrected || 0)) : 0;

  const features = regime?.features || {};
  const navItems = [
    { id: 'overview', label: 'Overview', desc: 'All panels', icon: Layers },
    { id: 'rainfall', label: 'Rainfall Map', desc: 'Spatial view', icon: Map },
    { id: 'probability', label: 'Probability', desc: 'Exceedance', icon: BarChart3 },
    { id: 'verification', label: 'Verification', desc: 'Skill scores', icon: CheckCircle },
  ];

  return (
    <aside className="w-full lg:w-[280px] bg-white border-r border-gray-100 overflow-y-auto flex-shrink-0">
      <div className="p-5 space-y-5">

        <div className="dashboard-card p-4">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                 style={{ backgroundColor: regimeInfo.color + '12' }}>
              {regimeInfo.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-bold text-[15px] text-gray-900 tracking-[-0.01em]">{regimeInfo.label}</div>
              <div className="text-[12px] text-gray-400 mt-0.5">Confidence: {(confidence * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Confidence</span>
              <span className="text-[13px] font-bold" style={{ color: regimeInfo.color }}>
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${confidence * 100}%`, backgroundColor: regimeInfo.color }} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'Wind Shear', value: `${features.wind_shear?.toFixed(1) || '18.2'} m/s`, color: '#0ea5e9' },
              { label: 'OLR', value: `${features.olr?.toFixed(1) || '-22.5'} W/m²`, color: '#f59e0b' },
              { label: 'CAPE', value: `${features.cape?.toFixed(0) || '1520'} J/kg`, color: '#ef4444' },
              { label: 'Vorticity', value: features.vorticity?.toFixed(1) || 'High', color: '#8b5cf6' },
            ].map((item) => (
              <div key={item.label} className="bg-gray-50 rounded-lg p-2.5">
                <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">{item.label}</div>
                <div className="text-[13px] font-bold text-gray-800">{item.value}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-card p-4">
          <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">Quick Stats</div>
          <div className="space-y-3">
            {[
              { label: 'Districts', value: districts.length, icon: '📍' },
              { label: 'Heavy Rain Alerts', value: heavyCount, icon: '⚠', color: heavyCount > 0 ? '#f59e0b' : undefined },
              { label: 'Max Forecast', value: `${maxRain.toFixed(0)} mm`, icon: '📊', color: '#ef4444' },
              { label: 'RMSE Reduction', value: '33%', icon: '↓', color: '#22c55e' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-[13px] text-gray-500">
                  <span className="text-sm">{item.icon}</span>
                  {item.label}
                </span>
                <span className="text-[14px] font-bold" style={{ color: item.color || '#0f172a' }}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2 px-1">Views</div>
          <div className="space-y-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-left transition-all duration-150 ${
                  activeView === item.id
                    ? 'bg-gray-900 text-white shadow-lg shadow-gray-900/20'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }`}
              >
                <item.icon className={`w-4 h-4 ${activeView === item.id ? 'text-white/80' : ''}`} />
                <div>
                  <div className="text-[13px] font-semibold">{item.label}</div>
                  <div className={`text-[11px] ${activeView === item.id ? 'text-white/50' : 'text-gray-400'}`}>
                    {item.desc}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {heavyCount > 0 && (
          <div className="rounded-xl bg-gradient-to-br from-amber-500/[0.08] to-orange-500/[0.08] border border-amber-200/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base">⚠</span>
              <span className="text-[13px] font-bold text-amber-800">Heavy Rain Alert</span>
            </div>
            <p className="text-[12px] text-amber-700/70 leading-relaxed">
              {heavyCount} district{heavyCount > 1 ? 's' : ''} with &gt;50% probability of heavy rainfall
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
