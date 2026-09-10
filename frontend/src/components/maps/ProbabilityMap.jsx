import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { indiaCenter, probabilityColorScale } from '../../data/mockData';
import 'leaflet/dist/leaflet.css';

export default function ProbabilityMap({ districts }) {
  return (
    <div className="dashboard-card p-0 overflow-hidden h-full flex flex-col">
      <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Heavy Rainfall Probability</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">P(Rainfall > 64.5mm) by district</p>
        </div>
        <div className="flex items-center gap-1.5">
          {[
            { label: '< 25%', color: '#bbf7d0' },
            { label: '25-50%', color: '#fde68a' },
            { label: '50-75%', color: '#fed7aa' },
            { label: '> 75%', color: '#fca5a5' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1 px-1.5 py-0.5 bg-gray-50 rounded text-[10px] font-medium text-gray-500">
              <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <MapContainer
          center={indiaCenter}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
          {districts.map((district) => {
            const pHeavy = district.p_heavy || 0;
            return (
              <CircleMarker
                key={district.district_id}
                center={[district.lat, district.lon]}
                radius={Math.max(7, Math.min(18, pHeavy * 20))}
                fillColor={probabilityColorScale(pHeavy)}
                color={pHeavy > 0.75 ? '#dc2626' : pHeavy > 0.5 ? '#f59e0b' : '#94a3b8'}
                weight={pHeavy > 0.5 ? 2 : 1}
                fillOpacity={0.85}
              >
                <Popup>
                  <div className="min-w-[180px]">
                    <div className="font-bold text-[14px] text-gray-900 mb-0.5">{district.name}</div>
                    <div className="text-[11px] text-gray-400 mb-2.5">{district.state}</div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-[12px]">
                        <span className="text-gray-400">P(R &gt; 7.5mm)</span>
                        <span className="font-semibold">{((district.p_moderate || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-[12px]">
                        <span className="text-gray-400">P(R &gt; 64.5mm)</span>
                        <span className="font-semibold text-amber-600">{(pHeavy * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-[12px]">
                        <span className="text-gray-400">P(R &gt; 124.5mm)</span>
                        <span className="font-semibold text-red-500">{((district.p_very_heavy || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-[12px]">
                        <span className="text-gray-400">P(R &gt; 244.5mm)</span>
                        <span className="font-semibold text-red-700">{((district.p_extreme || 0) * 100).toFixed(0)}%</span>
                      </div>
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
