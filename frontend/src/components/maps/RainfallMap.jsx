import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { useTheme } from '../../context/ThemeContext';

const indiaCenter = [20.5937, 78.9629];

const rainfallColorScale = (value) => {
  if (value < 7.5) return '#1e3a5f';
  if (value < 35) return '#1e6091';
  if (value < 64.5) return '#2196f3';
  if (value < 124.5) return '#f97316';
  return '#ef4444';
};

export default function RainfallMap({ districts = [], onDistrictClick }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`${isDark ? 'bg-slate-800/50 border-slate-700/30' : 'bg-white border-gray-200'} rounded-2xl border overflow-visible h-full flex flex-col`}>
      <div className={`px-5 py-3 border-b flex items-center justify-between ${isDark ? 'border-slate-700/30' : 'border-gray-100'}`}>
        <div>
          <h3 className={`text-[14px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Rainfall Forecast Map</h3>
          <p className={`text-[10px] mt-0.5 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>{districts.length} districts shown — click markers for details</p>
        </div>
        <div className="flex items-center gap-1">
          {[{ label: '<7.5', color: '#1e3a5f' }, { label: '7-35', color: '#1e6091' }, { label: '35-65', color: '#2196f3' }, { label: '65-125', color: '#f97316' }, { label: '>125', color: '#ef4444' }].map(item => (
            <div key={item.label} className="flex items-center gap-1 px-1 py-0.5 text-[9px] text-slate-400">
              <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <MapContainer center={indiaCenter} zoom={5} style={{ height: '100%', width: '100%' }} zoomControl={true}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {districts.map((d, i) => {
            const corrected = d.corrected || 0;
            const pHeavy = d.p_heavy || d.pHeavy || 0;
            return (
              <CircleMarker
                key={d.district_id || d.id || i}
                center={[d.lat, d.lon]}
                radius={Math.max(4, Math.min(14, corrected / 6))}
                fillColor={rainfallColorScale(corrected)}
                color={corrected > 64.5 ? '#ef4444' : isDark ? '#475569' : '#94a3b8'}
                weight={corrected > 64.5 ? 2 : 1}
                fillOpacity={0.85}
                eventHandlers={{ click: () => onDistrictClick?.(d) }}
              >
                <Popup>
                  <div className="min-w-[160px]">
                    <div className={`font-bold text-[13px] ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</div>
                    <div className={`text-[10px] mb-2 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{d.state}</div>
                    <div className="space-y-1 text-[11px]">
                      <div className="flex justify-between"><span className={isDark ? 'text-slate-400' : 'text-gray-500'}>Raw</span><span className="font-semibold">{d.raw} mm</span></div>
                      <div className="flex justify-between"><span className={isDark ? 'text-slate-400' : 'text-gray-500'}>Corrected</span><span className="font-bold text-blue-600">{d.corrected} mm</span></div>
                      <div className="flex justify-between"><span className={isDark ? 'text-slate-400' : 'text-gray-500'}>P(Heavy)</span><span className="font-semibold">{(pHeavy * 100).toFixed(0)}%</span></div>
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
