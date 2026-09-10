import { currentRegime, REGIMES, THRESHOLDS } from '../../data/mockData';
import { Wind, Droplets, Thermometer, Activity, Gauge, MapPin } from 'lucide-react';

export default function RegimePanel({ regime }) {
  const regimeType = regime?.type || currentRegime.type;
  const regimeInfo = REGIMES[regimeType] || REGIMES.active_monsoon;
  const confidence = regime?.confidence || currentRegime.confidence;
  const features = regime?.features || currentRegime.features;

  const featureList = [
    { key: 'wind_shear', label: 'Wind Shear', sub: '200-850 hPa', icon: Wind, color: '#0ea5e9', value: `${typeof features.wind_shear === 'number' ? features.wind_shear.toFixed(1) : features.windShear || '18.2'} m/s` },
    { key: 'olr', label: 'OLR Anomaly', sub: 'Central India', icon: Thermometer, color: '#f59e0b', value: `${typeof features.olr === 'number' ? features.olr.toFixed(1) : features.olr || '-22.5'} W/m²` },
    { key: 'cape', label: 'CAPE', sub: 'Instability index', icon: Activity, color: '#ef4444', value: `${typeof features.cape === 'number' ? features.cape.toFixed(0) : features.cape || '1520'} J/kg` },
    { key: 'vorticity', label: 'Low-Level Vorticity', sub: '850 hPa', icon: Gauge, color: '#8b5cf6', value: typeof features.vorticity === 'number' ? features.vorticity.toFixed(1) : features.vorticity || 'High' },
    { key: 'moisture_flux', label: 'Moisture Flux', sub: 'IVT magnitude', icon: Droplets, color: '#06b6d4', value: typeof features.moisture_flux === 'number' ? features.moisture_flux.toFixed(0) : features.moistureFlux || 'Strong' },
    { key: 'trough_position', label: 'Monsoon Trough', sub: 'Position', icon: MapPin, color: '#22c55e', value: features.trough_position || features.troughPosition || 'Gangetic Plains' },
  ];

  return (
    <div className="dashboard-card p-0 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 className="text-[16px] font-bold text-gray-900 tracking-[-0.01em]">Current Weather Regime</h2>
          <p className="text-[12px] text-gray-400 mt-0.5">Synoptic classification and indicators</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
               style={{ backgroundColor: regimeInfo.color + '12' }}>
            {regimeInfo.icon}
          </div>
          <div>
            <div className="text-[15px] font-bold text-gray-900">{regimeInfo.label}</div>
            <div className="text-[11px] text-gray-400">Active</div>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[12px] font-semibold text-gray-400 uppercase tracking-wider">Classification Confidence</span>
            <span className="text-[15px] font-bold" style={{ color: regimeInfo.color }}>
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${confidence * 100}%`, backgroundColor: regimeInfo.color }} />
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {featureList.map((f) => (
            <div key={f.key} className="group bg-gray-50/80 hover:bg-gray-50 rounded-xl p-3.5 transition-colors border border-transparent hover:border-gray-100">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: f.color + '10' }}>
                  <f.icon className="w-4 h-4" style={{ color: f.color }} />
                </div>
                <div>
                  <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">{f.label}</div>
                  <div className="text-[10px] text-gray-300">{f.sub}</div>
                </div>
              </div>
              <div className="text-[15px] font-bold text-gray-800 ml-[42px]">{f.value}</div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-5 border-t border-gray-100">
          <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">IMD Rainfall Thresholds</div>
          <div className="grid grid-cols-4 gap-2">
            {THRESHOLDS.map((t) => (
              <div key={t.name} className="text-center py-2.5 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
                <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: t.color + 'cc' }}>{t.name}</div>
                <div className="text-[13px] font-bold text-gray-700">{t.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
