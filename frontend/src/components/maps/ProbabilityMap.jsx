import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import { useTheme } from '../../context/ThemeContext';

const indiaCenter = [20.5937, 78.9629];
const indiaBounds = [[6.5, 68.0], [37.0, 97.5]];

function FitBounds({ districts }) {
  const map = useMap();
  useEffect(() => {
    if (districts.length > 0) {
      const lats = districts.map(d => d.lat).filter(Boolean);
      const lons = districts.map(d => d.lon).filter(Boolean);
      if (lats.length > 0 && lons.length > 0) {
        const bounds = [
          [Math.min(...lats) - 1, Math.min(...lons) - 1],
          [Math.max(...lats) + 1, Math.max(...lons) + 1]
        ];
        map.fitBounds(bounds, { padding: [20, 20] });
      }
    } else {
      map.fitBounds(indiaBounds);
    }
  }, [districts, map]);
  return null;
}

const probabilityColorScale = (value) => {
  if (value < 0.25) return '#22c55e';
  if (value < 0.50) return '#eab308';
  if (value < 0.75) return '#f97316';
  return '#ef4444';
};

export default function ProbabilityMap({ districts = [] }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`${isDark ? 'bg-slate-800/50 border-slate-700/30' : 'bg-white border-gray-200'} rounded-2xl border overflow-visible h-full flex flex-col`}>
      <div className={`px-5 py-3 border-b flex items-center justify-between ${isDark ? 'border-slate-700/30' : 'border-gray-100'}`}>
        <div>
          <h3 className={`text-[14px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Heavy Rainfall Probability Map</h3>
          <p className={`text-[10px] mt-0.5 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>P(Rainfall &gt; 64.5mm) by district</p>
        </div>
        <div className="flex items-center gap-1">
          {[{ label: '<25%', color: '#22c55e' }, { label: '25-50%', color: '#eab308' }, { label: '50-75%', color: '#f97316' }, { label: '>75%', color: '#ef4444' }].map(item => (
            <div key={item.label} className="flex items-center gap-1 px-1 py-0.5 text-[9px] text-slate-400">
              <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-[400px]">
        <MapContainer center={indiaCenter} zoom={5} minZoom={4} maxZoom={10} style={{ height: '100%', width: '100%' }} scrollWheelZoom={true}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitBounds districts={districts} />
          {districts.map((d, i) => {
            const pHeavy = d.p_heavy || d.pHeavy || 0;
            return (
              <CircleMarker
                key={d.district_id || d.id || i}
                center={[d.lat, d.lon]}
                radius={Math.max(4, Math.min(14, pHeavy * 18))}
                fillColor={probabilityColorScale(pHeavy)}
                color={pHeavy > 0.5 ? '#ef4444' : isDark ? '#475569' : '#94a3b8'}
                weight={pHeavy > 0.5 ? 2 : 1}
                fillOpacity={0.85}
              >
                <Popup>
                  <div className="min-w-[160px]">
                    <div className={`font-bold text-[13px] ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</div>
                    <div className={`text-[10px] mb-2 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{d.state}</div>
                    <div className="space-y-1 text-[11px]">
                      <div className="flex justify-between"><span className={isDark ? 'text-slate-400' : 'text-gray-500'}>P(&gt;7.5mm)</span><span>{((d.p_moderate || 0) * 100).toFixed(0)}%</span></div>
                      <div className="flex justify-between"><span className={isDark ? 'text-slate-400' : 'text-gray-500'}>P(&gt;64.5mm)</span><span className="font-semibold text-amber-600">{(pHeavy * 100).toFixed(0)}%</span></div>
                      <div className="flex justify-between"><span className={isDark ? 'text-slate-400' : 'text-gray-500'}>P(&gt;124.5mm)</span><span className="font-semibold text-red-500">{((d.p_very_heavy || 0) * 100).toFixed(0)}%</span></div>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
